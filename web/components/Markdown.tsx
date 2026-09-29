import type { ReactNode } from "react";

/** Just enough Markdown for CHANGELOG.md and quest text: bullets, **bold**, `code`, [links](url). */
function inline(text: string, key: number): ReactNode {
  const parts: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0, m: RegExpExecArray | null, i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const t = m[0];
    if (t.startsWith("**")) parts.push(<b key={`${key}-${i++}`}>{t.slice(2, -2)}</b>);
    else if (t.startsWith("`")) parts.push(<code key={`${key}-${i++}`}>{t.slice(1, -1)}</code>);
    else {
      const mm = /\[([^\]]+)\]\(([^)]+)\)/.exec(t)!;
      parts.push(<a key={`${key}-${i++}`} href={mm[2]} target="_blank" rel="noreferrer">{mm[1]}</a>);
    }
    last = m.index + t.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

export default function Markdown({ text }: { text: string }) {
  const lines = text.split(/\r?\n/);
  const out: ReactNode[] = [];
  let bullets: string[] = [];
  const flush = () => {
    if (bullets.length) {
      out.push(<ul className="plain" key={`ul-${out.length}`}>{bullets.map((b, i) => <li key={i}>{inline(b, i)}</li>)}</ul>);
      bullets = [];
    }
  };
  lines.forEach((ln, i) => {
    const t = ln.trim();
    if (/^[-*] /.test(t)) bullets.push(t.slice(2));
    else {
      flush();
      if (t) out.push(<p key={`p-${i}`}>{inline(t, i)}</p>);
    }
  });
  flush();
  return <div>{out}</div>;
}
