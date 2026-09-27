// Topics shown on the home page. Every question maps to a section of the
// knowledge base, so each one has a grounded answer.

export const SUGGESTIONS = [
  "What is TKDL and how does it stop wrongful patents?",
  "What happened in the turmeric patent case?",
  "आयुर्वेद में तीन दोष कौन से हैं?",
  "neem patent kyun cancel hua?",
];

export const TOPICS = [
  {
    id: "ayurveda",
    icon: "leaf",
    title: "Ayurveda Foundations",
    description: "Doshas, Prakriti and the classical texts behind Ayurveda.",
    questions: [
      "What are the three doshas in Ayurveda?",
      "What is Prakriti?",
      "Which classical texts form the Brihat Trayi?",
    ],
  },
  {
    id: "tkdl",
    icon: "book",
    title: "Traditional Knowledge & TKDL",
    description: "How India documents its heritage and defends it from misuse.",
    questions: [
      "What is the Traditional Knowledge Digital Library?",
      "How does TKDL help stop wrongful patents?",
      "What is biopiracy?",
    ],
  },
  {
    id: "patents",
    icon: "scale",
    title: "Patents & IP Law",
    description: "Patentability, prior art and what Indian law excludes.",
    questions: [
      "What makes an invention patentable?",
      "What is prior art in patent law?",
      "What does Section 3(p) of the Patents Act say?",
    ],
  },
  {
    id: "cases",
    icon: "landmark",
    title: "Landmark Cases",
    description: "Turmeric, neem, basmati and the disputes that shaped policy.",
    questions: [
      "Why was the US turmeric patent revoked?",
      "Why was the European neem patent revoked?",
      "What was the Basmati rice dispute with RiceTec?",
    ],
  },
  {
    id: "global",
    icon: "globe",
    title: "Global Frameworks",
    description: "TRIPS, the CBD, the Nagoya Protocol and benefit sharing.",
    questions: [
      "What is the TRIPS Agreement?",
      "What does the Nagoya Protocol cover?",
      "What is access and benefit sharing?",
    ],
  },
  {
    id: "search",
    icon: "search",
    title: "Prior-Art Search",
    description: "A step-by-step method to check if a formulation is already known.",
    questions: [
      "How can I check whether an Ayurvedic formulation is already prior art?",
      "What are IPC and CPC patent classification codes?",
      "How does Boolean search help in patent searching?",
    ],
  },
];
