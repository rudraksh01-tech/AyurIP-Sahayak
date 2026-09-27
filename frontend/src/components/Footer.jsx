import { GITHUB_URL } from "../links.js";
import { GitHubIcon, LeafIcon } from "./Icons.jsx";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <span className="brand-logo brand-logo-small">
            <LeafIcon size={15} />
          </span>
          <div>
            <strong>AyurIP Sahayak</strong>
            <span>Built by Rudra Pratap Singh · Powered by Gemini</span>
          </div>
        </div>

        <p className="footer-disclaimer">
          Educational research tool. Answers come only from the knowledge base
          and are not legal, patent or medical advice.
        </p>

        <a className="footer-link" href={GITHUB_URL} target="_blank" rel="noreferrer">
          <GitHubIcon size={16} />
          View source
        </a>
      </div>
    </footer>
  );
}
