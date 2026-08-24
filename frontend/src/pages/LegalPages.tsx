import React from 'react';

export const PrivacyPolicyPage: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button
        onClick={onBack}
        className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-medium transition-all"
      >
        ← Back to Mission Control
      </button>

      <div className="glass-card p-8 space-y-6">
        <div className="border-b border-slate-800 pb-4">
          <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded border border-amber-500/30">
            ⚠️ LEGAL NOTICE: STUB FOR COMPLIANCE BASELINE
          </span>
          <h1 className="text-2xl font-bold text-slate-100 mt-3">Privacy Policy</h1>
          <p className="text-xs text-slate-400 mt-1">Effective Date: August 24, 2026</p>
        </div>

        <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-100">1. Data Collection & Multi-Tenant Scoping</h2>
            <p>
              The DevOps Risk Platform processes organization deployment specifications, change titles, risk assessments, and team member email addresses strictly within tenant-isolated boundaries (`org_id`). Data is never shared or commingled across customer organizations.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-100">2. AI Vector Embeddings & Processing</h2>
            <p>
              Uploaded PDFs and change specifications are vectorized for RAG retrieval (`pgvector`). Vector indices are strictly scoped to the originating organization ID.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-100">3. Data Retention & Deletion Policy</h2>
            <p>
              Organizations retain full ownership of all submitted data. Upon written request or organization deletion, all associated change records, embeddings, notes, and audit logs are permanently purged from database storage.
            </p>
          </section>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 font-mono">
            DISCLAIMER: This document serves as a structural baseline template. Real legal review by qualified counsel is required prior to commercial SaaS deployment.
          </div>
        </div>
      </div>
    </div>
  );
};

export const TermsOfServicePage: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button
        onClick={onBack}
        className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-medium transition-all"
      >
        ← Back to Mission Control
      </button>

      <div className="glass-card p-8 space-y-6">
        <div className="border-b border-slate-800 pb-4">
          <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded border border-amber-500/30">
            ⚠️ LEGAL NOTICE: STUB FOR COMPLIANCE BASELINE
          </span>
          <h1 className="text-2xl font-bold text-slate-100 mt-3">Terms of Service</h1>
          <p className="text-xs text-slate-400 mt-1">Effective Date: August 24, 2026</p>
        </div>

        <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-100">1. Acceptance of Terms</h2>
            <p>
              By provisioning an account or accessing the DevOps Risk Platform, your organization agrees to these Terms of Service.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-100">2. AI Risk Evaluation Disclaimer</h2>
            <p>
              Automated risk analyses and recommendations are advisory tools designed to supplement engineering judgment. The platform assumes no liability for production outages or deployment failures.
            </p>
          </section>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 font-mono">
            DISCLAIMER: This document serves as a structural baseline template. Real legal review by qualified counsel is required prior to commercial SaaS deployment.
          </div>
        </div>
      </div>
    </div>
  );
};
