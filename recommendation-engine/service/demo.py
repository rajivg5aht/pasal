"""Separate, bounded storefront signals. Never reads Retailrocket artifacts or users."""
from collections import Counter
import hashlib
import json
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sklearn.feature_extraction.text import TfidfVectorizer
from switching.policy import PolicyConfig, recommend

class DemoProduct(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str = Field(pattern=r'^demo-[a-z0-9-]{1,60}$')
    title: str = Field(max_length=100)
    category: str = Field(max_length=50)
    description: str = Field(max_length=1000)
    attributes: list[str] = Field(max_length=8)
    eligible: bool

class DemoProfile(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    personalization: bool = False
    event_count: int = Field(default=0, ge=0)
    recent_items: list[str] = Field(default_factory=list, max_length=20)
    seen_items: list[str] = Field(default_factory=list, max_length=1000)
    selected_categories: list[str] = Field(default_factory=list, max_length=12)

class DemoRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    products: list[DemoProduct] = Field(max_length=100)
    # Anonymous distinct-item profiles, from consenting demo users only.
    profiles: list[list[str]] = Field(max_length=5000)
    profile: DemoProfile
    k: int = Field(default=4, ge=1, le=10)

    @model_validator(mode='after')
    def validate_profiles(self):
        if len({p.id for p in self.products}) != len(self.products):
            raise ValueError('Duplicate catalogue IDs')
        for row in self.profiles:
            if len(row) > 20 or len(set(row)) != len(row):
                raise ValueError('Require at most 20 distinct profile items')
        all_ids = [i for row in self.profiles for i in row]+self.profile.recent_items+self.profile.seen_items
        import re
        if any(not re.fullmatch(r'demo-[a-z0-9-]{1,60}', i) for i in all_ids):
            raise ValueError('Only demonstration IDs accepted')
        if len(set(self.profile.recent_items)) != len(self.profile.recent_items):
            raise ValueError('Duplicate recent items')
        if not set(self.profile.recent_items) <= set(self.profile.seen_items):
            raise ValueError('Seen items must include recent history')
        if self.profile.event_count < len(set(self.profile.seen_items)):
            raise ValueError('Inconsistent event count')
        return self

def recommend_demo(request: DemoRequest, policy: PolicyConfig):
    products = sorted(request.products, key=lambda p: p.id)
    mapping = {p.id: i for i,p in enumerate(products)}
    eligible = {i for i,p in enumerate(products) if p.eligible}
    active = request.profile.personalization
    history = [mapping[i] for i in request.profile.recent_items if i in mapping] if active else []
    seen = {mapping[i] for i in request.profile.seen_items if i in mapping} if active else set()
    categories = request.profile.selected_categories if active else []
    events = request.profile.event_count if active else 0
    support = Counter()
    pairs = Counter()
    for profile in request.profiles:
        row = sorted({mapping[i] for i in profile if i in mapping})
        support.update(row)
        pairs.update((a,b) for a in row for b in row if a != b)
    cf = Counter()
    usable = 0
    candidates = eligible-seen
    for item in history:
        neighbours = {b: n/np.sqrt(support[a]*support[b]) for (a,b),n in pairs.items()
                      if a == item and b in candidates}
        usable += bool(neighbours)
        cf.update(neighbours)
    confidence = usable/len(history) if history else 0.
    content = {}
    if history and products:
        texts = [' '.join([p.title,p.category,p.description,*p.attributes]) for p in products]
        try:
            matrix = TfidfVectorizer().fit_transform(texts)
            vector = np.asarray(matrix[history].mean(axis=0)).ravel()
            norm = np.linalg.norm(vector)
            if norm:
                values = np.asarray(matrix @ (vector/norm)).ravel()
                content = {i: float(v) for i,v in enumerate(values) if v > 0}
        except ValueError as exc:
            if 'empty vocabulary' not in str(exc): raise
    signals = {'global_popularity':dict(support),
               'category_popularity':{i:n for i,n in support.items() if products[i].category in categories},
               'item_cf':dict(cf), 'content':content}
    result = recommend(events,seen,eligible,categories,confidence,signals,policy,k=request.k)
    fallback = result['fallback_reason']
    strategy = result['strategy']
    items = result['items']
    if not items and candidates:
        # Explicit, unscored cold catalogue fallback; never invent popularity.
        preferred = sorted(i for i in candidates if products[i].category in categories)
        items = (preferred or sorted(candidates))[:request.k]
        fallback = 'insufficient_demo_evidence'
        strategy = 'catalogue_fallback'
    reasons = {
        'global_popularity':'Frequently present in consented demonstration browsing profiles.',
        'category_popularity':'In your selected category, ranked by consented demo profile support.',
        'content':'Text similarity to products in your consented demonstration browsing history.',
        'item_cf':'Products co-viewed in consented demonstration profiles.',
        'cf_popularity_hybrid':'A blend of demo co-viewing evidence and profile popularity.',
        'hybrid_fallback':'Limited collaborative confidence; using demo co-viewing and popularity evidence.',
        'catalogue_fallback':'Catalogue suggestion: there is not enough demonstration activity to rank this by a model.',
    }
    return {'items':[{'productId':products[i].id,'reason':reasons[strategy]} for i in items],
            'strategy':strategy,'fallback':fallback,'personalized':active,'genai_used':False,
            'source':'synthetic_demo','configuration':'demo_switching_v1',
            'configuration_status':'Research-selected policy transferred to demo data; not validated on the demo population',
            'catalogue_sha256':hashlib.sha256(json.dumps([p.model_dump() for p in products],sort_keys=True).encode()).hexdigest(),
            'profile_count':len(request.profiles),'candidate_count':len(candidates),
            'routing':{'history_event_count':events,'cf_confidence':confidence},
            'limitations':'Uses up to 5000 latest consented profiles and 20 recent distinct items per profile. No Retailrocket items or generated demo text.'}
