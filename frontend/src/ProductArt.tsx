import { useState } from "react";
import shoeImages from "../../catalogue/shoe-images.json";
export default function ProductArt({
  kind,
  title,
}: {
  kind: string;
  title: string;
}) {
  const [failed, setFailed] = useState<string | null>(null);
  const photo = shoeImages[kind as keyof typeof shoeImages];
  if (photo) return <figure className="shoe-photo">
    {failed === kind ? <p role="status">Product photograph unavailable</p> :
      <img src={photo.url} alt={photo.title} loading="lazy" referrerPolicy="no-referrer"
        onError={() => setFailed(kind)} style={{ width: "100%", height: "240px", objectFit: "contain" }} />}
    <figcaption><a href={photo.source} target="_blank" rel="noreferrer">Photo source</a>
      {" · "}<a href={photo.license} target="_blank" rel="noreferrer">{photo.credit}</a></figcaption>
  </figure>;
  const shapes: Record<string, React.ReactNode> = {
    bag: (
      <>
        <path d="M65 90h110l12 112H53z" />
        <path d="M90 92V72a30 30 0 0160 0v20" />
      </>
    ),
    mug: (
      <>
        <path d="M65 80h95v85a32 32 0 01-32 32H97a32 32 0 01-32-32z" />
        <path d="M160 95h15a25 25 0 010 50h-15M85 58v-16m32 16v-22m30 22v-16" />
      </>
    ),
    bottle: (
      <>
        <path d="M100 40h40v35l15 20v107H85V95l15-20z" />
        <path d="M100 55h40M85 112h70M85 172h70" />
      </>
    ),
    notebook: (
      <>
        <rect x="65" y="40" width="115" height="166" rx="8" />
        <path d="M85 40v166M103 82h54m-54 20h54m-54 20h40" />
      </>
    ),
    scarf: (
      <>
        <path d="M70 45h55v150H70zM125 45l45 30-30 118-35-12" />
        <path d="M75 195v15m15-15v15m15-15v15m15-15v15M72 85h50m-50 50h50" />
      </>
    ),
    lamp: (
      <>
        <path d="M83 44h74l30 78H53zM120 122v73m-45 10h90M165 120v27" />
      </>
    ),
    basket: (
      <>
        <path d="M50 100h140l-20 102H70zM70 100a50 50 0 01100 0" />
        <path d="M59 140h122M65 171h110M90 101l8 99m44-99-8 99" />
      </>
    ),
    tea: (
      <>
        <rect x="65" y="60" width="110" height="145" rx="8" />
        <path d="M65 79h110M74 53h92" />
        <path d="M110 153q-15-38 31-46 10 40-31 46zm0 0 26-35" />
      </>
    ),
  };
  return (
    <svg
      viewBox="0 0 240 240"
      role="img"
      aria-label={`${title} — illustrative synthetic product`}
      className="demo-art"
    >
      <circle cx="120" cy="122" r="99" fill="#e6e9dc" />
      <g
        fill="#f6f0df"
        stroke="#426455"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {shapes[kind] || shapes.bag}
      </g>
    </svg>
  );
}
