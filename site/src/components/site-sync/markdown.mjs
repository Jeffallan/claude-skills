// Text helpers for site-sync. No dependencies, so the handbook's tests can import them.

// Index of every line that sits outside a fenced code block. A fence opens with ``` or ~~~
// (three or more) and closes only with the same character, at least as many times.
function linesOutsideFences(lines) {
  const outside = [];
  let fence = null;
  lines.forEach((line, i) => {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})/)?.[1];
    if (fence) {
      if (
        marker &&
        marker[0] === fence[0] &&
        marker.length >= fence.length &&
        !line.trim().slice(marker.length).trim()
      ) {
        fence = null;
      }
    } else if (marker) {
      fence = marker;
    } else {
      outside.push(i);
    }
  });
  return outside;
}

function h1Index(lines) {
  return linesOutsideFences(lines).find((i) => /^#\s+\S/.test(lines[i])) ?? -1;
}

/** The first H1 outside code fences, or null. */
export function findH1(body) {
  const lines = body.split('\n');
  const i = h1Index(lines);
  return i < 0 ? null : lines[i].replace(/^#\s+/, '').trim();
}

/** The body without the H1 that findH1 returns, and without the blank lines after it. */
export function removeH1(body) {
  const lines = body.split('\n');
  const i = h1Index(lines);
  if (i < 0) return body;
  let end = i + 1;
  while (end < lines.length - 1 && !lines[end].trim()) end++;
  lines.splice(i, end - i);
  return lines.join('\n');
}

/**
 * Whole sentences from the start of `text`, as many as fit in `max` characters. The first
 * sentence is kept whole even when it alone is longer. A sentence ends at . ! or ? followed by
 * a space and a capital letter, or at the end of the text.
 */
export function firstSentences(text, max) {
  const flat = text.replace(/\s*\n\s*/g, ' ').trim();
  const ends = [...flat.matchAll(/[.!?](?=\s+[A-Z]|$)/g)].map((m) => m.index + 1);
  if (!ends.length) return flat;
  const fit = ends.filter((e) => e <= max);
  return flat.slice(0, fit.length ? fit.at(-1) : ends[0]);
}

/** The body, trimmed, with any of `endLines` peeled off its end, in any order. */
export function stripTrailingLines(body, endLines) {
  let out = body.trimEnd();
  let changed = true;
  while (changed) {
    changed = false;
    for (const line of endLines) {
      if (
        line &&
        out.endsWith(line) &&
        (out.length === line.length || out[out.length - line.length - 1] === '\n')
      ) {
        out = out.slice(0, -line.length).trimEnd();
        changed = true;
      }
    }
  }
  return out;
}
