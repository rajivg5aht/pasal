import { useEffect, useState } from "react";
import App from "./App";
import DemoShop from "./DemoShop";
import Admin from "./Admin";
export default function Root() {
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    const change = () => setHash(location.hash);
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, []);
  if (hash === "#admin") return <Admin />;
  if (hash === "#research" || hash.startsWith("#research-"))
    return (
      <>
        <div className="research-mode">
          <a href="#">← Demo shop</a>
          <strong>Research Lab · Anonymous Retailrocket items</strong>
          <span>
            No real product identities or prices. Live profiles are separate
            from frozen experiments.
          </span>
        </div>
        <App />
      </>
    );
  return <DemoShop />;
}
