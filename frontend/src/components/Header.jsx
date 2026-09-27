import { GITHUB_URL } from "../links.js";
import { GitHubIcon, LeafIcon, MoonIcon, PlusIcon, SunIcon } from "./Icons.jsx";

const STATUS_LABELS = {
  checking: "Connecting…",
  online: "Online",
  offline: "Offline",
};

export default function Header({ health, hasMessages, onNewChat, theme, onToggleTheme }) {
  return (
    <header className="header">
      <div className="header-inner">
        <button className="brand" onClick={onNewChat} aria-label="AyurIP Sahayak home">
          <span className="brand-logo">
            <LeafIcon size={19} />
          </span>
          <span className="brand-text">
            <span className="brand-name">AyurIP Sahayak</span>
            <span className="brand-tagline">Ayurveda · Traditional Knowledge · IPR</span>
          </span>
        </button>

        <div className="header-actions">
          <span
            className={`status status-${health.status}`}
            title={health.status === "online" ? `Online · model ${health.model}` : STATUS_LABELS[health.status]}
          >
            <span className="status-dot" />
            <span className="hide-mobile">{STATUS_LABELS[health.status]}</span>
          </span>

          {hasMessages && (
            <button className="button" onClick={onNewChat}>
              <PlusIcon size={16} />
              <span className="hide-mobile">New chat</span>
            </button>
          )}

          <button
            className="icon-button"
            onClick={onToggleTheme}
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            title={theme === "dark" ? "Light theme" : "Dark theme"}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>

          <a
            className="icon-button"
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            aria-label="Source code on GitHub"
          >
            <GitHubIcon />
          </a>
        </div>
      </div>
    </header>
  );
}
