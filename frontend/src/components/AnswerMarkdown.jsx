import Markdown from "react-markdown";

// "[1]" or "[2, 4]" that is not already a Markdown link
const CITATION_GROUP = /\[(\d+(?:\s*,\s*\d+)*)\](?!\()/g;

// Turn citations into links so the Markdown renderer hands them to
// renderLink(), which draws them as clickable chips.
function linkCitations(text) {
  return text.replace(CITATION_GROUP, (_, numbers) =>
    numbers
      .split(",")
      .map((number) => `[${number.trim()}](#cite-${number.trim()})`)
      .join("")
  );
}

export default function AnswerMarkdown({ text, sourceCount, onCite }) {
  const renderLink = ({ href, children }) => {
    const citation = href?.match(/^#cite-(\d+)$/);

    if (!citation) {
      return (
        <a href={href} target="_blank" rel="noreferrer">
          {children}
        </a>
      );
    }

    const number = Number(citation[1]);

    if (number < 1 || number > sourceCount) {
      return <span>[{children}]</span>;
    }

    return (
      <button
        type="button"
        className="cite"
        onClick={() => onCite(number)}
        aria-label={`Show source ${number}`}
      >
        {number}
      </button>
    );
  };

  return (
    <div className="answer-markdown">
      <Markdown components={{ a: renderLink }}>{linkCitations(text)}</Markdown>
    </div>
  );
}
