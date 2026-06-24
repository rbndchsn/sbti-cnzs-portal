const QA_URL = "data/qa.json";

const MIN_SUGGEST_SCORE = 2.0;
const STRONG_MATCH_SCORE = 6.0;
const MAX_RESULTS = 7;

const stopWords = new Set([
  "a","an","and","are","as","at","be","by","can","could","did","do","does",
  "for","from","had","has","have","how","i","if","in","is","it","its","me",
  "my","of","on","or","our","should","the","their","there","they","this",
  "to","was","we","what","when","where","which","who","why","will","with",
  "would","you","your"
]);

let qaData = [];
let currentResults = [];

const $ = (id) => document.getElementById(id);

function normalize(text) {
  return String(text || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(text) {
  return normalize(text)
    .split(" ")
    .map(t => t.trim())
    .filter(t => t.length > 1 && !stopWords.has(t));
}

function uniqueTokens(tokens) {
  return [...new Set(tokens)];
}

function itemSearchText(item) {
  return [
    item.question,
    ...(item.alternate_questions || []),
    ...(item.tags || []),
    item.source,
    item.source_section,
    item.answer
  ].join(" ");
}

function scoreItem(query, item) {
  const queryNorm = normalize(query);
  const questionNorm = normalize(item.question);
  const altNorm = normalize((item.alternate_questions || []).join(" "));
  const tagNorm = normalize((item.tags || []).join(" "));

  const queryTokens = uniqueTokens(tokenize(query));
  const questionTokens = uniqueTokens(tokenize(item.question));
  const altTokens = uniqueTokens(tokenize((item.alternate_questions || []).join(" ")));
  const tagTokens = uniqueTokens(tokenize((item.tags || []).join(" ")));
  const allTokens = uniqueTokens(tokenize(itemSearchText(item)));

  if (!queryTokens.length) return 0;

  let score = 0;

  // Exact or phrase-like matches should rank highest, but still only show as suggestions.
  if (queryNorm === questionNorm) score += 10;
  if (questionNorm.includes(queryNorm) && queryNorm.length >= 4) score += 4;
  if (altNorm.includes(queryNorm) && queryNorm.length >= 4) score += 3;
  if (tagNorm.includes(queryNorm) && queryNorm.length >= 3) score += 2;

  // Weighted token overlap.
  for (const token of queryTokens) {
    if (questionTokens.includes(token)) score += 2.0;
    else if (altTokens.includes(token)) score += 1.5;
    else if (tagTokens.includes(token)) score += 1.2;
    else if (allTokens.includes(token)) score += 0.6;
  }

  // Reward coverage of the user's meaningful words.
  const matched = queryTokens.filter(token => allTokens.includes(token)).length;
  const coverage = matched / queryTokens.length;
  score += coverage * 2;

  return Number(score.toFixed(3));
}

function getRankedResults(query, items = qaData) {
  return items
    .map(item => ({ ...item, score: scoreItem(query, item) }))
    .filter(item => item.score >= MIN_SUGGEST_SCORE)
    .sort((a, b) => b.score - a.score || a.question.localeCompare(b.question))
    .slice(0, MAX_RESULTS);
}

function showMessage(text, type = "info") {
  const el = $("message");
  el.textContent = text;
  el.className = `message visible ${type}`;
}

function clearMessage() {
  const el = $("message");
  el.textContent = "";
  el.className = "message";
}

function renderResults(results, query = "") {
  const container = $("results");
  currentResults = results;

  if (!query.trim()) {
    container.className = "results empty-state";
    container.textContent = "Type a question above or select a tag.";
    $("resultsTitle").textContent = "Suggested questions";
    clearMessage();
    return;
  }

  if (!results.length) {
    container.className = "results empty-state";
    container.innerHTML = `
      <strong>No approved question found.</strong>
      <p>The standard or database does not contain strong keyword overlap with your question.</p>
      <p>Try reformulating, using terminology from the source document, or browsing the tags.</p>
    `;
    $("resultsTitle").textContent = "No approved match";
    showMessage("No approved question was found. The site will not guess. Try different wording or browse the tags.", "warning");
    saveLocalNoMatch(query);
    return;
  }

  $("resultsTitle").textContent = results[0].score >= STRONG_MATCH_SCORE
    ? "Are you looking for one of these approved questions?"
    : "Possible related approved questions";

  showMessage("Select the approved question that best matches what you meant. The portal will not auto-answer.", "info");

  container.className = "results";
  container.innerHTML = results.map((item, index) => `
    <button class="result-card" data-id="${escapeHtml(item.id)}">
      <span class="score-pill">match ${item.score}</span>
      <strong>${escapeHtml(item.question)}</strong>
      <div class="result-meta">
        ${escapeHtml((item.tags || []).join(" • "))} 
        ${item.source ? " — " + escapeHtml(item.source) : ""}
      </div>
    </button>
  `).join("");

  container.querySelectorAll(".result-card").forEach(btn => {
    btn.addEventListener("click", () => {
      const selected = qaData.find(item => item.id === btn.dataset.id);
      if (selected) showAnswer(selected);
    });
  });
}

function formatAnswer(raw) {
  const text = String(raw || "");
  // Split on the PDF bullet marker "O " that starts a new bullet item.
  // The pattern looks for " O " (space-O-space) or a leading "O " at the start.
  const parts = text.split(/\s+O\s+/);
  if (parts.length <= 1) {
    // No bullets detected — render as plain paragraphs.
    return parts[0].split(/\n{2,}/).map(p => `<p>${p.trim()}</p>`).join("");
  }
  // First segment is the intro paragraph (before the first bullet).
  const intro = parts[0].trim() ? `<p>${parts[0].trim()}</p>` : "";
  const items = parts.slice(1).map(item => `<li>${item.trim()}</li>`).join("");
  return `${intro}<ul>${items}</ul>`;
}

function showAnswer(item) {
  $("answerQuestion").textContent = item.question;
  $("answerText").innerHTML = formatAnswer(item.answer);
  $("answerText").classList.remove("answer-placeholder");
  $("answerSource").textContent = item.source || "Not specified";
  $("answerSection").textContent = item.source_section || "Not specified";
  $("answerOwner").textContent = item.owner || "Not specified";
  $("answerReviewed").textContent = item.last_reviewed || "Not specified";
  $("answerVersion").textContent = item.version || "Not specified";
  $("feedbackMessage").textContent = "";
  $("answerMeta").hidden = false;
  $("answerFeedback").hidden = false;
  $("clearAnswer").hidden = false;
  $("answerCard").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderTags() {
  const MIN_COUNT = 3;
  const counts = new Map();
  qaData.forEach(item => (item.tags || []).forEach(tag => {
    const norm = tag.trim().toLowerCase();
    if (norm) counts.set(norm, (counts.get(norm) || 0) + 1);
  }));

  const tags = [...counts.entries()]
    .filter(([, n]) => n >= MIN_COUNT)
    .sort((a, b) => a[0].localeCompare(b[0]));
  const container = $("tagCloud");

  const reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const useSphere = !reduceMotion && tags.length > 2 &&
    typeof window.startTagSphere === "function";

  container.className = useSphere ? "tag-cloud tag-cloud--sphere" : "tag-cloud";
  container.innerHTML = tags.map(([tag, count]) => `
    <button class="tag" data-tag="${escapeHtml(tag)}" title="${escapeHtml(tag)} (${count})">${escapeHtml(tag)}${useSphere ? "" : " (" + count + ")"}</button>
  `).join("");

  container.querySelectorAll(".tag").forEach(btn => {
    btn.addEventListener("click", () => {
      const tag = btn.dataset.tag;
      $("searchInput").value = tag;
      renderResults(getRankedResults(tag), tag);
    });
  });

  if (useSphere) {
    if (window.__tagSphere && window.__tagSphere.stop) window.__tagSphere.stop();
    window.__tagSphere = window.startTagSphere(container, { speed: 0.4, idle: 0.15, fontMultiplier: 11 });
  }
}

function renderPopularQuestions() {
  const PAGE_SIZE = 10;
  const container = $("popularQuestions");
  const total = qaData.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  if (renderPopularQuestions.page == null) renderPopularQuestions.page = 0;
  if (renderPopularQuestions.page >= totalPages) renderPopularQuestions.page = 0;
  const page = renderPopularQuestions.page;

  const start = page * PAGE_SIZE;
  const pageItems = qaData.slice(start, start + PAGE_SIZE);

  const buttons = pageItems.map(item => `
    <button class="question-button" data-id="${escapeHtml(item.id)}">
      ${escapeHtml(item.question)}
    </button>
  `).join("");

  let pager = "";
  if (total > PAGE_SIZE) {
    const from = start + 1;
    const to = Math.min(start + PAGE_SIZE, total);
    pager = `
    <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:14px;">
      <button id="popPrev" class="secondary">&#8592; Back 10</button>
      <span style="color:var(--muted);font-size:.9rem;">${from}-${to} of ${total}</span>
      <button id="popNext" class="secondary">Next 10 &#8594;</button>
    </div>`;
  }

  container.innerHTML = buttons + pager;

  container.querySelectorAll(".question-button").forEach(btn => {
    btn.addEventListener("click", () => {
      const selected = qaData.find(item => item.id === btn.dataset.id);
      if (selected) showAnswer(selected);
    });
  });

  const prev = $("popPrev");
  const next = $("popNext");
  if (prev) prev.addEventListener("click", () => {
    renderPopularQuestions.page = (page - 1 + totalPages) % totalPages;
    renderPopularQuestions();
  });
  if (next) next.addEventListener("click", () => {
    renderPopularQuestions.page = (page + 1) % totalPages;
    renderPopularQuestions();
  });
}

function saveLocalNoMatch(query) {
  try {
    const key = "approvedAnswerPortalNoMatches";
    const existing = JSON.parse(localStorage.getItem(key) || "[]");
    existing.push({
      timestamp: new Date().toISOString(),
      question: query
    });
    localStorage.setItem(key, JSON.stringify(existing.slice(-200)));
  } catch (err) {
    // Local logging is best-effort only.
  }
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadData() {
  const response = await fetch(QA_URL);
  if (!response.ok) throw new Error(`Could not load ${QA_URL}`);
  qaData = await response.json();

  renderTags();
  renderPopularQuestions();
  renderResults([], "");
}

function runSearch() {
  const query = $("searchInput").value;
  renderResults(getRankedResults(query), query);
}

document.addEventListener("DOMContentLoaded", () => {
  $("searchButton").addEventListener("click", runSearch);
  $("searchInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") runSearch();
  });
  $("searchInput").addEventListener("input", () => {
    const query = $("searchInput").value;
    if (query.trim().length >= 3) {
      renderResults(getRankedResults(query), query);
    } else if (!query.trim()) {
      renderResults([], "");
    }
  });
  $("clearAnswer").addEventListener("click", () => {
    $("answerQuestion").textContent = "";
    $("answerText").innerHTML = "The expert-approved answer will appear here, with its source section and metadata.";
    $("answerText").classList.add("answer-placeholder");
    $("answerMeta").hidden = true;
    $("answerFeedback").hidden = true;
    $("clearAnswer").hidden = true;
  });
  document.querySelectorAll("[data-feedback]").forEach(btn => {
    btn.addEventListener("click", () => {
      $("feedbackMessage").textContent = "Feedback noted locally in this browser for the demo. For production, collect feedback in Google Sheets, Forms, or a backend.";
    });
  });

  loadData().catch(err => {
    console.error(err);
    showMessage("Could not load the Q&A database. Make sure you are serving the /public folder with a local web server.", "warning");
  });
});
