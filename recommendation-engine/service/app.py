"""Internal recommendation API. Bind to localhost; Express owns user authentication."""
from contextlib import asynccontextmanager
import hmac
import json
import os
from pathlib import Path
import threading
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
import pandas as pd

from evaluation.common import Case
from genai.explanations import explain
from models.engine import RecommendationEngine
from models.content.train_snapshot import fingerprint
from switching.policy import PolicyConfig

ROOT = Path(__file__).resolve().parents[2]


class Profile(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    personalization: bool = False
    event_count: int = Field(default=0, ge=0)
    recent_items: list[int] = Field(default_factory=list, max_length=20)
    seen_items: list[int] = Field(default_factory=list, max_length=100000)
    selected_categories: list[str] = Field(default_factory=list, max_length=30)
    k: int = Field(default=10, ge=1, le=50)

    @model_validator(mode='after')
    def consistent(self):
        if any(i < 0 for i in self.recent_items+self.seen_items):
            raise ValueError('Item IDs must be nonnegative')
        if len(set(self.recent_items)) != len(self.recent_items):
            raise ValueError('Recent items must be unique, oldest to newest')
        if not set(self.recent_items) <= set(self.seen_items):
            raise ValueError('Full seen set must include the profile')
        if self.event_count < len(set(self.seen_items)):
            raise ValueError('Event count cannot be smaller than unique seen items')
        return self


def load_runtime():
    config_path=ROOT/'data/processed/validation-tuning-v1/selected_config.json'
    config=json.loads(config_path.read_text())
    train_path=ROOT/'data/splits/event-count-v1/train.csv'
    enriched_path = os.environ.get('PASAL_ENRICHED_ARTIFACT_DIR')
    content_path = Path(enriched_path).resolve() if enriched_path else ROOT/'data/processed/content-event-count-v1'
    engine=RecommendationEngine(pd.read_csv(train_path),config['cutoff_ms'],
        content_path,ROOT/'data/processed/cf-event-count-v1')
    config['serving_configuration'] = 'switching_without_genai'
    if enriched_path:
        if engine.content_manifest.get('kind') != 'historical_properties_plus_reviewed_generative_text':
            raise ValueError('Enriched serving requires a verified GenAI artifact')
        if engine.content_manifest['base_manifest_sha256'] != fingerprint(ROOT/'data/processed/content-event-count-v1/manifest.json'):
            raise ValueError('Enriched model does not extend the serving baseline')
        config['reviewed_descriptions'] = json.loads((content_path/'reviewed_descriptions.json').read_text())
        config['serving_configuration'] = 'switching_with_genai' 
    if engine.cf_manifest['train_sha256'] != fingerprint(train_path):
        raise ValueError('Training/model fingerprint mismatch')
    return engine,config


def create_app(runtime=None, token=None):
    service_token=token if token is not None else os.environ.get('RECOMMENDATION_SERVICE_TOKEN','')
    if len(service_token)<32:
        raise ValueError('Configure a random RECOMMENDATION_SERVICE_TOKEN of at least 32 characters')
    gate=threading.BoundedSemaphore(2)

    @asynccontextmanager
    async def lifespan(app):
        app.state.runtime=runtime if runtime is not None else load_runtime()
        yield
        app.state.runtime=None

    app=FastAPI(title='Pasal internal recommendation service',version='0.1.0',lifespan=lifespan)

    def authenticate(x_service_token: Annotated[str | None, Header()] = None):
        if x_service_token is None or not hmac.compare_digest(x_service_token,service_token):
            raise HTTPException(401,'Invalid service credentials')

    @app.get('/health')
    def health():
        return {'status':'ready' if getattr(app.state,'runtime',None) else 'starting'}

    @app.post('/recommendations',dependencies=[Depends(authenticate)])
    def recommendations(profile:Profile):
        if not gate.acquire(blocking=False):
            raise HTTPException(503,'Recommendation capacity busy; try again shortly')
        try:
            started=time.perf_counter()
            engine,config=app.state.runtime
            # Consent disabled: discard history AND preference evidence, not merely
            # hide its use in the explanation. Profiles are never persisted here.
            case=Case(0,profile.event_count if profile.personalization else 0,
                      tuple(profile.recent_items) if profile.personalization else (),
                      frozenset(profile.seen_items) if profile.personalization else frozenset(),frozenset())
            categories=profile.selected_categories if profile.personalization else []
            signals,confidence,selected=engine.signals(case,selected_categories=categories)
            configuration = config.get('serving_configuration', 'switching_without_genai')
            items,strategy=engine.predict(case,signals,confidence,selected,configuration,
                                         PolicyConfig(**config['switching']),config['fixed_weights'],profile.k)
            descriptions = config.get('reviewed_descriptions', {})
            explained = []
            for item in items:
                entry = descriptions.get(str(item))
                explained.append(explain(item, strategy, entry['generation'], entry['review']) if entry else explain(item, strategy))
            description_count = sum(item['description_source'] == 'reviewed_generative_api' for item in explained)
            generated_ranking_used = configuration == 'switching_with_genai' and strategy == 'content'
            return {'items':explained,
                    'strategy':strategy,'personalized':profile.personalization,
                    'model_cutoff_ms':config['cutoff_ms'],
                    'genai_used':generated_ranking_used or description_count > 0,
                    'genai_ranking_used':generated_ranking_used,
                    'genai_description_count':description_count,
                    'configuration':configuration,
                    'configuration_status':config['status'],
                    'latency_ms':round((time.perf_counter()-started)*1000,3)}
        finally:
            gate.release()
    return app
