"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Link href="/" className="text-2xl font-bold text-gradient">TradeQuest</Link>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link href="/features" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Features
                </Link>
                <Link href="/pricing" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Pricing
                </Link>
                <Link href="/docs" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Docs
                </Link>
                <Link href="/auth" className="bg-brand-bright-yellow text-brand-dark-teal hover:bg-brand-bright-yellow/90 px-4 py-2 rounded-md text-sm font-medium">
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <Link href="/" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Privacy Policy
            </h1>
            <p className="text-lg text-gray-600">
              Last updated: September 28, 2025
            </p>
          </motion.div>
        </div>
      </section>

      {/* Content */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="prose prose-lg max-w-none"
          >
            <div className="space-y-8">
              <div>
                <p className="text-gray-600 leading-relaxed mb-6">
                  Tradequest Technologies Inc., d/b/a "TradeQuest" ("TradeQuest," "we," "us," or "our") provides this Privacy Policy to explain how we collect, use, share, and protect information when you access our websites, apps, APIs, and related services (collectively, the "Service").
                </p>
                <p className="text-gray-600 leading-relaxed mb-6">
                  If you do not agree with this Privacy Policy, please do not use the Service.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Who we are (controller):</h2>
                <div className="text-gray-600 leading-relaxed">
                  <p><strong>Tradequest Technologies Inc. (d/b/a TradeQuest)</strong></p>
                  <p>1007 N Orange St, 4th Floor, Suite #4242, Wilmington, Delaware 19801, United States</p>
                  <p>Support: support@tradequest.tech • Privacy: privacy@tradequest.tech</p>
                  <p>Website: https://tradequest.tech</p>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">1) Scope</h2>
                <p className="text-gray-600 leading-relaxed">
                  This Policy covers personal information we process when you use the Service or interact with us (e.g., support). It does not cover third-party websites, services, or practices that we do not control.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">2) Information we collect</h2>
                <div className="text-gray-600 leading-relaxed space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">A) You provide to us</h3>
                    <ul className="list-disc pl-6 space-y-2">
                      <li><strong>Account & contact:</strong> email, alias, timezone, display preferences.</li>
                      <li><strong>Security:</strong> optional password, 2FA/TOTP setup (stored as hashed/secret values).</li>
                      <li><strong>Trading data:</strong> trade logs, notes, tags, uploaded files/screenshots, journal entries.</li>
                      <li><strong>Broker API keys (read-only):</strong> keys you provide to connect your broker/exchange. We instruct users to never grant withdrawal/transfer permissions. Keys are stored encrypted.</li>
                      <li><strong>Preferences:</strong> goals, risk rules, discipline settings, notification and AI/backtesting preferences.</li>
                      <li><strong>Support:</strong> messages and attachments you send to support@tradequest.tech.</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">B) Automatically collected</h3>
                    <ul className="list-disc pl-6 space-y-2">
                      <li><strong>Device/technical:</strong> IP address, browser/OS, device identifiers, language, referring/exit pages.</li>
                      <li><strong>Usage & events:</strong> pages viewed, features used, timestamps, error logs, job metrics (e.g., imports, backtests).</li>
                      <li><strong>Cookies & similar:</strong> essential session cookies, preference cookies, and (if enabled) privacy-centric analytics cookies. See "Cookies & Tracking" below.</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">C) From third parties</h3>
                    <ul className="list-disc pl-6 space-y-2">
                      <li><strong>Payments:</strong> limited transaction metadata from our payment processor (e.g., Stripe). We do not store full card numbers.</li>
                      <li><strong>Messaging:</strong> your Telegram user ID when you link alerts.</li>
                      <li><strong>Brokers/exchanges:</strong> fills/positions when you connect read-only keys.</li>
                    </ul>
                    <p className="mt-3">
                      We do not intentionally collect special/sensitive categories of data (e.g., health, biometric). Please avoid uploading others' personal data without permission.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">3) How we use information</h2>
                <ul className="text-gray-600 leading-relaxed list-disc pl-6 space-y-2">
                  <li><strong>Provide the Service:</strong> authenticate accounts, import and normalize broker data, journal/analytics/backtests, alerts, reports, account administration.</li>
                  <li><strong>Improve & secure:</strong> monitor performance, debug issues, detect/prevent abuse, develop features, maintain availability.</li>
                  <li><strong>Communicate:</strong> transactional emails (logins, receipts, alerts), service messages, responses to support.</li>
                  <li><strong>Marketing (optional):</strong> send product updates or promotions only if you opt in; unsubscribe anytime.</li>
                  <li><strong>Legal compliance & protection:</strong> enforce Terms, comply with law, and protect rights, property, and safety.</li>
                </ul>
                
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">AI features</h3>
                  <p className="text-sm text-blue-800">
                    To deliver AI-powered analyses (e.g., trade context summaries), we may process relevant data (such as candles around a trade, trade logs) with an AI provider under contract. For quality improvement, we use anonymized telemetry only if you opt in. AI outputs may be inaccurate—use judgment.
                  </p>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">4) Legal bases (EEA/UK where applicable)</h2>
                <ul className="text-gray-600 leading-relaxed list-disc pl-6 space-y-2">
                  <li><strong>Contract:</strong> to provide and administer the Service you request.</li>
                  <li><strong>Legitimate interests:</strong> security, improvement, fraud prevention, analytics compatible with user expectations.</li>
                  <li><strong>Consent:</strong> marketing emails and optional anonymized telemetry.</li>
                  <li><strong>Legal obligations:</strong> tax, accounting, compliance, and responding to lawful requests.</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">5) Sharing & disclosures</h2>
                <p className="text-gray-600 leading-relaxed mb-3">
                  We share personal information only as described below and with appropriate safeguards:
                </p>
                <div className="space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Service providers / subprocessors (on our behalf):</h3>
                    <ul className="text-gray-600 leading-relaxed list-disc pl-6 space-y-1 mt-2">
                      <li><strong>Payments:</strong> Stripe (billing and receipts).</li>
                      <li><strong>Email delivery:</strong> a reputable email service for login links/receipts/alerts.</li>
                      <li><strong>Error tracking & logging:</strong> a reputable provider to diagnose issues.</li>
                      <li><strong>Product analytics (privacy-centric):</strong> to understand feature usage at an aggregate level.</li>
                      <li><strong>AI processing:</strong> a hosted AI API provider to generate requested analyses.</li>
                      <li><strong>Messaging:</strong> Telegram Bot API (if you link).</li>
                      <li><strong>Hosting/infra & storage:</strong> US-based compute and storage providers.</li>
                    </ul>
                    <p className="text-gray-600 mt-2">These providers are bound by contracts limiting use of your data to providing services to us.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Legal/compliance:</h3>
                    <p className="text-gray-600">if required by law or in response to a lawful request, to protect our rights or users' safety, or to enforce our Terms.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Corporate transactions:</h3>
                    <p className="text-gray-600">in connection with merger, acquisition, financing, or sale of assets (we will continue to protect personal data and notify you of material changes).</p>
                  </div>
                </div>
                <p className="text-gray-600 mt-3 font-medium">
                  We do not "sell" or "share" personal information for cross-context behavioral advertising (as those terms are defined under US state privacy laws).
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">6) International transfers</h2>
                <p className="text-gray-600 leading-relaxed">
                  We primarily store and process data in the United States. When personal data is transferred internationally, we use appropriate safeguards (e.g., Standard Contractual Clauses) where required by law.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">7) Retention</h2>
                <p className="text-gray-600 leading-relaxed">
                  We retain personal information for as long as necessary to provide the Service, comply with legal obligations, resolve disputes, and enforce agreements. Backups are generally retained for about 30 days. You can request deletion at any time (see "Your Rights").
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">8) Your choices & controls</h2>
                <ul className="text-gray-600 leading-relaxed list-disc pl-6 space-y-2">
                  <li><strong>Access & edits:</strong> manage most info in the app; contact privacy@tradequest.tech if you need help.</li>
                  <li><strong>Marketing emails:</strong> opt in/out in settings or via the unsubscribe link. Transactional emails (e.g., login links, receipts) are required.</li>
                  <li><strong>Cookies & Tracking:</strong> you can control cookies via your browser. Essential cookies are required for login/session.</li>
                  <li><strong>Telemetry for improvement:</strong> off by default; you may opt in or out at any time.</li>
                  <li><strong>Broker keys:</strong> you can revoke access at any time from Integrations; we will stop syncing and delete stored keys.</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">9) Your rights</h2>
                <p className="text-gray-600 leading-relaxed mb-3">
                  Depending on where you live, you may have rights such as access, correction, deletion, portability, restriction, and objection.
                </p>
                <div className="space-y-2">
                  <p className="text-gray-600"><strong>How to exercise:</strong> email privacy@tradequest.tech with your request. We may ask for information to verify your identity.</p>
                  <p className="text-gray-600"><strong>Response time:</strong> we aim to respond within 30 days; for California, within 45 days (extendable as permitted).</p>
                  <p className="text-gray-600"><strong>California (CCPA/CPRA):</strong> we do not sell/share personal information, nor use or disclose "sensitive personal information" for purposes requiring a right to limit. You have rights to know, delete, correct, and non-discrimination.</p>
                  <p className="text-gray-600"><strong>EEA/UK (GDPR):</strong> you may also lodge a complaint with your local data protection authority.</p>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">10) Cookies & tracking</h2>
                <div className="space-y-3">
                  <p className="text-gray-600">We use:</p>
                  <ul className="text-gray-600 leading-relaxed list-disc pl-6 space-y-2">
                    <li><strong>Essential cookies:</strong> for authentication, security, and core functionality.</li>
                    <li><strong>Preferences:</strong> to remember settings like theme/timezone.</li>
                    <li><strong>Analytics (first-party or privacy-centric):</strong> to measure aggregate usage (no cross-site advertising tracking).</li>
                  </ul>
                  <p className="text-gray-600 mt-3">
                    Do Not Track/GPC: We don't use data for cross-context behavioral advertising. Where applicable, we treat Global Privacy Control signals as an opt-out of such processing.
                  </p>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">11) Security</h2>
                <p className="text-gray-600 leading-relaxed">
                  We use reasonable technical and organizational measures, including:
                </p>
                <ul className="text-gray-600 leading-relaxed list-disc pl-6 space-y-1 mt-2">
                  <li>Encryption in transit (TLS) and at rest for sensitive fields (e.g., AES-GCM for broker keys).</li>
                  <li>httpOnly, secure cookies, CSRF protections, rate limiting, access controls, and audit logging.</li>
                  <li>Least-privilege access for staff and systems.</li>
                </ul>
                <p className="text-gray-600 mt-3">
                  No method is 100% secure. If we learn of a breach affecting your data, we will notify you without undue delay consistent with applicable law.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">12) Children's privacy</h2>
                <p className="text-gray-600 leading-relaxed">
                  The Service is not intended for children under 16. If you believe we have collected data from a child under 16, contact privacy@tradequest.tech and we will delete it.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">13) Third-party links</h2>
                <p className="text-gray-600 leading-relaxed">
                  The Service may link to third-party sites or services. Their privacy practices are governed by their own policies; we are not responsible for them.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">14) Changes to this Policy</h2>
                <p className="text-gray-600 leading-relaxed">
                  We may update this Policy from time to time. If we make material changes, we will provide notice (e.g., email or in-app). The "Last updated" date reflects the latest version.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">15) Contact us</h2>
                <div className="text-gray-600 leading-relaxed">
                  <p><strong>Tradequest Technologies Inc. (d/b/a TradeQuest)</strong></p>
                  <p>1007 N Orange St, 4th Floor, Suite #4242</p>
                  <p>Wilmington, Delaware 19801, United States</p>
                  <p>Support: support@tradequest.tech • Privacy: privacy@tradequest.tech</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold text-gradient mb-4">TradeQuest</h3>
              <p className="text-gray-400">
                The trading platform that focuses on education, discipline, and continuous improvement.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/features" className="hover:text-white">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-white">Pricing</Link></li>
                <li><Link href="/docs" className="hover:text-white">Documentation</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                <li><Link href="/careers" className="hover:text-white">Careers</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/disclaimer" className="hover:text-white">Risk Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 TradeQuest. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
