/* ==========================================================================
   TRIAD Index — Scoring Engine
   Ported from the gate-based ReadinessScorer in trl_assessment_gui_v4.py
   Score = the highest level whose full gate of category minimums is met.
   ========================================================================== */

const CATEGORIES = {
  "Technology": {
    axis: "TRL",
    max: 5,
    levels: [
      "Basic principles have been observed through scientific research",
      "Applied research has begun and practical application(s) have been identified",
      "Preliminary testing of technology components has begun, and technical feasibility has been established in a laboratory environment",
      "Initial testing of integrated product/system has been completed in a laboratory environment",
      "Laboratory-scale integrated product/system demonstrates performance in the intended application(s)"
    ]
  },
  "Product Development": {
    axis: "TRL",
    max: 5,
    levels: [
      "Product/system has not yet been validated at pilot scale",
      "Pilot-scale product/system has been tested in the intended application(s)",
      "Demonstration of a full-scale product/system prototype has been completed in the intended application(s)",
      "Actual product/system has been proven to work in its near-final form under representative conditions",
      "Product/system is in final form and has been operated under the full range of operating conditions"
    ]
  },
  "Manufacturing Research": {
    axis: "MRL",
    max: 5,
    levels: [
      "Work to identify manufacturing approach and cost model has not begun or is incomplete",
      "Applied research to analyze properties and availability of materials for manufacturing is underway",
      "Materials and processes have been evaluated for manufacturability using experiments or models",
      "Manufacturing risks, cost drivers, performance parameters, and required investments have been identified",
      "Prototype components produced in a production-relevant environment; scale-up planning has begun"
    ]
  },
  "Manufacturing Scale-up": {
    axis: "MRL",
    max: 6,
    levels: [
      "The full manufacturing approach has not yet been demonstrated in a production-relevant environment",
      "A preliminary manufacturing system design exists; further changes are required for a successful demonstration",
      "The manufacturing system has been demonstrated in a representative environment; detailed design nearing completion",
      "A detailed manufacturing system design is complete and stable enough to enter low-rate production",
      "Low-rate production has been achieved; ready to enter full-rate production with minimal design changes",
      "Full-rate production has been demonstrated to meet performance, quality, and reliability requirements"
    ]
  },
  "Product Definition/Design": {
    axis: "CRL",
    max: 6,
    levels: [
      "Knowledge of potential applications is limited",
      "Product ideas based on the new technology may exist, but are speculative and unvalidated",
      "One or more initial product hypotheses have been defined",
      "Mapping product/system attributes against customer needs has produced a clear value proposition",
      "A comprehensive customer value proposition model exists, including design specs, certifications, and trade-offs",
      "Final design optimization is complete, certifications obtained, and detailed requirements incorporated"
    ]
  },
  "Competitive Landscape": {
    axis: "CRL",
    max: 5,
    levels: [
      "Knowledge of market constraints is limited",
      "Market research is derived mainly from secondary sources; basic competitive understanding exists",
      "Comprehensive market research proving commercial feasibility is complete; intermediate competitive understanding",
      "Competitive analysis illustrating unique features and advantages versus competing products is complete",
      "Full and complete understanding of the competitive landscape, target applications, and market has been achieved"
    ]
  },
  "Team": {
    axis: "CRL",
    max: 5,
    levels: [
      "No team or company in place (single individual, no legal entity)",
      "Solely technical or non-technical founder(s) running the company with no outside assistance",
      "Founder(s) running the company with assistance from outside advisors/mentors and/or an accelerator",
      "Balanced team with technical and commercialization experience, assisted by outside advisors",
      "Balanced team with all capabilities onboard (sales, marketing, ops, etc.), assisted by outside advisors"
    ]
  },
  "Go-To-Market": {
    axis: "CRL",
    max: 6,
    levels: [
      "Value proposition has not yet been developed",
      "Initial business model and value proposition have been defined",
      "Customers/partners interviewed to understand pain points; model refined based on their feedback",
      "Market and customer needs mapped to product requirements; initial stakeholder relationships developed",
      "Partnerships formed with key stakeholders across the value chain (suppliers, partners, customers)",
      "Supply agreements with suppliers and partners are in place"
    ]
  },
  "Supply Chain": {
    axis: "CRL",
    max: 6,
    levels: [
      "Potential suppliers and customers have not yet been identified",
      "Potential suppliers, partners, and customers identified and mapped in an initial value-chain analysis",
      "Relationships established with suppliers/partners/customers, who have given input on requirements",
      "Manufacturing process qualifications (QC/QA) have been defined and are in progress",
      "Products/systems have been pilot-manufactured and sold to initial customers",
      "Full-scale manufacturing and widespread deployment to customers has been achieved"
    ]
  },
  "Finance": {
    axis: "CRL",
    max: 7,
    levels: [
      "Non-dilutive funding sources, such as grants, have been sought or obtained",
      "Funding needs have been identified based on business model and financial plan",
      "Potential sources of external financing have been identified",
      "The company is being pitched to private investors with a plan including revenue projections",
      "Private investment has been raised",
      "Purchase orders from customers have been received",
      "Revenue is being collected via paid purchase orders"
    ]
  }
};

// Gate requirements — the highest level whose full requirement set is met wins.
const TRL_RULES = {
  1: { "Technology": 1 },
  2: { "Technology": 2 },
  3: { "Technology": 3 },
  4: { "Technology": 4 },
  5: { "Technology": 5 },
  6: { "Technology": 5, "Product Development": 2 },
  7: { "Technology": 5, "Product Development": 3 },
  8: { "Technology": 5, "Product Development": 4 },
  9: { "Technology": 5, "Product Development": 5 }
};

const CRL_RULES = {
  1: { "Product Definition/Design": 1, "Competitive Landscape": 1, "Team": 1, "Go-To-Market": 1, "Supply Chain": 1, "Finance": 1 },
  2: { "Product Definition/Design": 2, "Competitive Landscape": 2, "Team": 2, "Go-To-Market": 1, "Supply Chain": 1, "Finance": 1 },
  3: { "Product Definition/Design": 3, "Competitive Landscape": 3, "Team": 2, "Go-To-Market": 2, "Supply Chain": 1, "Finance": 1 },
  4: { "Product Definition/Design": 4, "Competitive Landscape": 4, "Team": 3, "Go-To-Market": 3, "Supply Chain": 2, "Finance": 2 },
  5: { "Product Definition/Design": 5, "Competitive Landscape": 5, "Team": 3, "Go-To-Market": 4, "Supply Chain": 3, "Finance": 3 },
  6: { "Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 4, "Go-To-Market": 5, "Supply Chain": 3, "Finance": 4 },
  7: { "Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 4, "Go-To-Market": 6, "Supply Chain": 4, "Finance": 5 },
  8: { "Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 5, "Go-To-Market": 6, "Supply Chain": 5, "Finance": 6 },
  9: { "Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 5, "Go-To-Market": 6, "Supply Chain": 6, "Finance": 7 }
};

const MRL_RULES = {
  1: { "Manufacturing Research": 1, "Technology": 1 },
  2: { "Manufacturing Research": 2, "Technology": 2 },
  3: { "Manufacturing Research": 3, "Technology": 3 },
  4: { "Manufacturing Research": 4, "Technology": 4 },
  5: { "Manufacturing Research": 5, "Technology": 5 },
  6: { "Manufacturing Research": 5, "Manufacturing Scale-up": 2, "Technology": 5, "Product Development": 2 },
  7: { "Manufacturing Research": 5, "Manufacturing Scale-up": 3, "Technology": 5, "Product Development": 3 },
  8: { "Manufacturing Research": 5, "Manufacturing Scale-up": 4, "Technology": 5, "Product Development": 3 },
  9: { "Manufacturing Research": 5, "Manufacturing Scale-up": 5, "Technology": 5, "Product Development": 4 },
  10: { "Manufacturing Research": 5, "Manufacturing Scale-up": 6, "Technology": 5, "Product Development": 5 }
};

const AXIS_MAX = { TRL: 9, MRL: 10, CRL: 9 };

const IMPACT_WEIGHTS = {
  "Technology": 1.0,
  "Product Development": 0.9,
  "Manufacturing Scale-up": 0.8,
  "Finance": 0.7,
  "Team": 0.6
};
const DEFAULT_IMPACT = 0.5;

const BENCHMARKS = {
  "Early Stage": { TRL: 4, MRL: 3, CRL: 3 },
  "Growth Stage": { TRL: 6, MRL: 5, CRL: 5 },
  "Established": { TRL: 8, MRL: 7, CRL: 7 }
};

function scoreFromRules(selections, rules) {
  let best = 0;
  Object.keys(rules).map(Number).sort((a, b) => a - b).forEach((level) => {
    const req = rules[level];
    const met = Object.entries(req).every(([cat, min]) => (selections[cat] || 0) >= min);
    if (met) best = level;
  });
  return best;
}

function gapsForLevel(selections, rules, level) {
  const req = rules[level] || {};
  const gaps = {};
  Object.entries(req).forEach(([cat, min]) => {
    const cur = selections[cat] || 0;
    if (cur < min) gaps[cat] = [cur, min];
  });
  return gaps;
}

function nextStep(selections, rules, currentLevel) {
  const target = currentLevel + 1;
  if (!rules[target]) return null;
  return { target, gaps: gapsForLevel(selections, rules, target) };
}

function computeScores(selections) {
  return {
    TRL: scoreFromRules(selections, TRL_RULES),
    MRL: scoreFromRules(selections, MRL_RULES),
    CRL: scoreFromRules(selections, CRL_RULES)
  };
}

function identifyCriticalGaps(selections, scores) {
  const gaps = [];
  [["TRL", TRL_RULES], ["MRL", MRL_RULES], ["CRL", CRL_RULES]].forEach(([axis, rules]) => {
    const current = scores[axis];
    const maxLevel = Math.max(...Object.keys(rules).map(Number));
    for (let level = current + 1; level <= maxLevel; level++) {
      const req = rules[level] || {};
      Object.entries(req).forEach(([cat, min]) => {
        const cur = selections[cat] || 0;
        if (cur < min) {
          gaps.push({
            category: cat, axis, gap: min - cur,
            impact: IMPACT_WEIGHTS[cat] ?? DEFAULT_IMPACT,
            required: min, current: cur
          });
        }
      });
    }
  });
  gaps.sort((a, b) => (b.impact - a.impact) || (b.gap - a.gap));
  // de-duplicate by category, keep first (closest/highest-impact) occurrence
  const seen = new Set();
  return gaps.filter((g) => {
    const key = g.category + g.axis;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ------------------------------------------------------------------------
// Illustrative sample case studies (placeholder scores for demonstration)
// ------------------------------------------------------------------------
const CASE_STUDIES = [
  {
    id: "weevil",
    name: "Red Palm Weevil Eradication Device",
    sector: "AgTech / Hardware",
    blurb: "An acoustic-detection and targeted-treatment device for early-stage pest control in date and palm agriculture.",
    selections: {
      "Technology": 5, "Product Development": 2,
      "Manufacturing Research": 3, "Manufacturing Scale-up": 1,
      "Product Definition/Design": 3, "Competitive Landscape": 3, "Team": 3,
      "Go-To-Market": 2, "Supply Chain": 2, "Finance": 2
    },
    takeaway: "Technology is validated (TRL 6) well ahead of manufacturing and go-to-market — a classic hardware-startup profile where the bottleneck to funding readiness is production and commercial proof, not the core science."
  },
  {
    id: "iot-energy",
    name: "Energy Harvesting for IoT Sensors",
    sector: "IoT / Deep Tech",
    blurb: "A self-powering energy-harvesting module that eliminates battery replacement for distributed wireless sensor networks.",
    selections: {
      "Technology": 5, "Product Development": 3,
      "Manufacturing Research": 5, "Manufacturing Scale-up": 2,
      "Product Definition/Design": 4, "Competitive Landscape": 4, "Team": 3,
      "Go-To-Market": 3, "Supply Chain": 2, "Finance": 3
    },
    takeaway: "Technology and manufacturing are both maturing in step (TRL 7, MRL 6) — the gap is commercial: go-to-market and finance are the levers that would move CRL fastest."
  },
  {
    id: "ai-power",
    name: "AI-Based Power Saving",
    sector: "Software / AI",
    blurb: "A machine-learning optimization layer that reduces industrial power consumption by predicting and shaping demand.",
    selections: {
      "Technology": 5, "Product Development": 4,
      "Manufacturing Research": 1, "Manufacturing Scale-up": 1,
      "Product Definition/Design": 5, "Competitive Landscape": 5, "Team": 4,
      "Go-To-Market": 4, "Supply Chain": 3, "Finance": 4
    },
    takeaway: "MRL sits at 1 not because of weakness, but because manufacturing barely applies to a pure software product. This is where the methodology needs customization — MRL should be down-weighted or excluded entirely for software ventures, exactly as the framework's customization step intends."
  }
];
