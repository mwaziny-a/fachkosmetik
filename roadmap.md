# FaceInsight AI — Product Roadmap

---

## Phase 1: Core (Current)
- [x] Image quality validation
- [x] InsightFace + OpenCV face detection
- [x] GPT-4o Vision cosmetic analysis
- [x] Priority-ranked recommendations (8 categories)
- [x] Structured JSON + readable report
- [x] Streamlit premium UI
- [x] FastAPI REST backend

---

## Phase 2: User Layer
- [ ] **User accounts & authentication** — JWT-based auth, social login (Google, Apple)
- [ ] **Analysis history** — store past reports per user, timeline view
- [ ] **Before/after comparison** — side-by-side report diff across sessions
- [ ] **User profile memory** — store skin type, preferences, prior treatments for context-aware future analyses

## Phase 3: Monetization
- [ ] **Subscription tiers** — Free (1 analysis/month), Pro ($19/mo, unlimited), Clinic ($99/mo, white-label)
- [ ] **Stripe integration** — recurring billing, usage metering
- [ ] **API access tier** — rate-limited API keys for B2B clients
- [ ] **Credit system** — pay-per-analysis option for occasional users

## Phase 4: Operations
- [ ] **Admin dashboard** — user management, usage overview, flagged analyses review
- [ ] **Analytics & logging** — per-endpoint latency, OpenAI token usage, conversion tracking
- [ ] **Recommendation scoring system** — allow users to rate recommendation usefulness; feed back into prompt tuning
- [ ] **A/B prompt testing** — versioned prompts with performance tracking

## Phase 5: B2B / Clinic Growth
- [ ] **Clinic lead generation flow** — "Book a consultation" CTA linked to partner clinics based on top recommendations
- [ ] **White-label product** — skincare brand integrations; recommend specific SKUs tied to observed concerns
- [ ] **EMR-adjacent export** — PDF report export for clinic intake
- [ ] **Clinic portal** — aesthetic practices upload patient photos pre-consult

## Phase 6: SaaS Architecture
- [ ] **Multi-tenant architecture** — isolated data per organization
- [ ] **Webhook events** — notify downstream systems when analysis completes
- [ ] **Self-hosted option** — on-premise deployment for enterprise/medical clients with data residency requirements
- [ ] **Audit logging** — GDPR-compliant data access logs
- [ ] **Model versioning** — pin prompt + model version per analysis for reproducibility

---

## Technical Debt & Hardening
- Add Redis caching for repeated image hashes (identical image = cached result)
- Replace polling with WebSocket for real-time analysis progress
- Add image EXIF stripping before sending to OpenAI (privacy)
- Rate limiting per IP / per user token
- Automated prompt regression tests against a curated image set