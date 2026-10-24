/**
 * Label-overlap audit for the graph panel.
 *
 * Paste into the browser console on the Explore page (or evaluate it through a
 * driver) and call `auditTop20()`. For every one of the top 20 candidate families
 * it opens the family, renders both the default view and the all-paths view, and
 * reports:
 *   - label/label overlaps   (two node captions colliding)
 *   - label/node overlaps    (a caption sitting on top of some other node)
 *   - edge-through-label     (an edge segment crossing a caption's box)
 * A clean run prints zero for all three on every family.
 */
const overlaps = (a, b) => a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2;

function segmentHitsRect(p, q, r) {
  if (Math.max(p.x, q.x) < r.x1 || Math.min(p.x, q.x) > r.x2) return false;
  if (Math.max(p.y, q.y) < r.y1 || Math.min(p.y, q.y) > r.y2) return false;
  const side = (x, y) => (q.x - p.x) * (y - p.y) - (q.y - p.y) * (x - p.x);
  const corners = [[r.x1, r.y1], [r.x2, r.y1], [r.x2, r.y2], [r.x1, r.y2]].map(([x, y]) => side(x, y));
  return corners.some(v => v > 0) && corners.some(v => v < 0);
}

function auditCurrent(label) {
  const cy = document.querySelector('.graph-canvas')._cyreg.cy;
  const nodes = cy.nodes().map(n => ({
    name: n.data('full'),
    label: n.renderedBoundingBox({includeLabels: true, includeNodes: false, includeEdges: false}),
    body: n.renderedBoundingBox({includeLabels: false}),
  }));
  const report = {view: label, nodes: nodes.length, labelLabel: [], labelNode: [], edgeLabel: []};
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      if (overlaps(nodes[i].label, nodes[j].label)) report.labelLabel.push([nodes[i].name, nodes[j].name]);
    }
    for (const other of nodes) {
      if (other !== nodes[i] && overlaps(nodes[i].label, other.body)) report.labelNode.push([nodes[i].name, other.name]);
    }
  }
  cy.edges().forEach(e => {
    const p = e.source().renderedPosition(), q = e.target().renderedPosition();
    nodes.forEach(n => {
      if (n.name === e.source().data('full') || n.name === e.target().data('full')) return;
      if (segmentHitsRect(p, q, n.label)) report.edgeLabel.push([e.data('label'), n.name]);
    });
  });
  return report;
}

async function auditTop20() {
  const cards = [...document.querySelectorAll('.candidate')].slice(0, 20);
  const results = [];
  for (const card of cards) {
    const name = card.querySelector('.candidate-title').textContent.trim();
    card.click();
    await new Promise(r => setTimeout(r, 2200));
    results.push({family: name, ...auditCurrent('default')});
    const showAll = [...document.querySelectorAll('.path-selector button')].find(b => b.textContent.startsWith('Show all'));
    if (showAll) showAll.click();
    const context = document.querySelector('.check input');
    if (!context.checked) context.click();
    await new Promise(r => setTimeout(r, 2200));
    results.push({family: name, ...auditCurrent('all-paths + context')});
  }
  const flagged = results.filter(r => r.labelLabel.length || r.labelNode.length || r.edgeLabel.length);
  return {families: cards.length, views: results.length, flagged, clean: results.length - flagged.length};
}
