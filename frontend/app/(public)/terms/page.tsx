"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";

export default function TermsPage() {
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
              Terms of Service
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
                  These Terms of Service ("Terms") are a binding agreement between Tradequest Technologies Inc., a Delaware corporation, d/b/a TradeQuest ("Company," "we," "us," or "our") and you ("you" or "User"). By accessing or using our websites, apps, APIs, or related services (collectively, the "Service"), you agree to these Terms. If you do not agree, do not use the Service.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">1) What we do (educational software; not a broker)</h2>
                <p className="text-gray-600 leading-relaxed">
                  We provide subscription software for trade journaling, analytics, backtesting, and AI-assisted reviews via read-only broker integrations (the "Platform"). We do not provide investment, legal, tax, accounting, or other professional advice, and we are not a broker-dealer, investment adviser, exchange, ATS, or money transmitter. The Service is educational and for information only.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">2) Eligibility; accounts; security</h2>
                <div className="text-gray-600 leading-relaxed space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Age.</h3>
                    <p>You must be 16+ to use the Service. If you are under 18, you may use the Service only with parent/guardian consent and where permitted by law.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Account security.</h3>
                    <p>You are responsible for maintaining the confidentiality of your credentials, enabling 2FA, and all activity under your account. Notify us promptly of unauthorized use.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Accuracy.</h3>
                    <p>You agree your registration and profile information is accurate and kept updated.</p>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">3) Subscriptions; billing; refunds</h2>
                <div className="text-gray-600 leading-relaxed space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Charge timing.</h3>
                    <p>Paid plans are billed at checkout (monthly or annual) in USD via our payment processor (e.g., Stripe). Taxes may apply.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Auto-renewal & cancellation.</h3>
                    <p>Subscriptions renew until canceled in your Account. Cancellation stops future renewals; it doesn't refund time already used unless our refund policy applies.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Refund policy (baseline).</h3>
                    <p>First-time purchases are refundable within 7 days upon request to support@tradequest.tech. Renewals are generally non-refundable except where required by law.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Price/features changes.</h3>
                    <p>We may change prices or features prospectively; we'll notify you before changes affecting your next renewal.</p>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">4) Strict "no advice" + risk disclosures</h2>
                <div className="text-gray-600 leading-relaxed space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">No advice or recommendations.</h3>
                    <p>Content, analytics, and AI outputs are not investment advice or a solicitation to buy/sell any security, digital asset, or instrument.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">No guarantees.</h3>
                    <p>Backtests and simulations are hypothetical and may differ materially from actual results. Past performance is not indicative of future results.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Your risk.</h3>
                    <p>Trading involves risk, including total loss. You alone are responsible for your trades and outcomes.</p>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">5) Broker connections; data sources</h2>
                <div className="text-gray-600 leading-relaxed space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Read-only keys only.</h3>
                    <p>Integrations require read-only API keys. Never grant withdrawal/transfer permissions. You are responsible for key management.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Third parties.</h3>
                    <p>Broker APIs, market data, and third-party services are outside our control and may be inaccurate, delayed, incomplete, or unavailable.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">No execution.</h3>
                    <p>We do not place, route, or execute orders.</p>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">6) Acceptable use</h2>
                <p className="text-gray-600 leading-relaxed">
                  You agree not to: (a) use the Service for unlawful purposes or market abuse; (b) violate third-party terms or IP rights; (c) scrape at scale or reverse engineer; (d) circumvent security or plan limits; (e) upload malware or unlawful content; (f) attempt to access others' accounts or data. We may suspend or terminate access for violations or to protect the Service and users.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">7) Ownership; your license to use</h2>
                <p className="text-gray-600 leading-relaxed">
                  We and our licensors own the Service (software, designs, data excluding your content). Subject to these Terms and payment of fees, we grant you a limited, revocable, nonexclusive, nontransferable license to use the Service for personal or internal business educational use.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">8) Your content; license to us</h2>
                <p className="text-gray-600 leading-relaxed">
                  You retain rights to content you upload (e.g., trade logs, notes, files). You grant us a worldwide, royalty-free license to host, process, analyze, display, and create derivative insights solely to operate and improve the Service; comply with law; and enforce these Terms. You represent you have rights to your content.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">9) AI features; model outputs</h2>
                <p className="text-gray-600 leading-relaxed">
                  AI may produce inaccurate or offensive outputs. Verify results before relying on them. You are responsible for how you use AI outputs. We may use anonymized telemetry to improve quality only if you opt in (see Privacy Policy).
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">10) Beta/preview features</h2>
                <p className="text-gray-600 leading-relaxed">
                  Alpha/beta features may be unstable or changed/removed. Use at your sole risk.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">11) Feedback</h2>
                <p className="text-gray-600 leading-relaxed">
                  If you give feedback, you grant us a perpetual, irrevocable, worldwide license to use it without restriction or compensation.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">12) Privacy</h2>
                <p className="text-gray-600 leading-relaxed">
                  Our Privacy Policy is incorporated by reference and explains how we collect, use, and share data.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">13) Third-party links/services</h2>
                <p className="text-gray-600 leading-relaxed">
                  We are not responsible for third-party websites, services, or terms.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">14) Export & sanctions</h2>
                <p className="text-gray-600 leading-relaxed">
                  You will not use the Service in violation of export-control or sanctions laws and represent you are not located in, or a resident of, embargoed or sanctioned jurisdictions (including Cuba, Iran, North Korea, Syria, and the Crimea/Donetsk/Luhansk regions of Ukraine) or otherwise on a restricted list.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">15) Disclaimers</h2>
                <p className="text-gray-600 leading-relaxed font-medium">
                  TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, OR STATUTORY (INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, ACCURACY, AVAILABILITY). WE DO NOT WARRANT RESULTS, ANALYTICS, OR AI OUTPUTS WILL BE ERROR-FREE OR UNINTERRUPTED.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">16) Limitation of liability</h2>
                <p className="text-gray-600 leading-relaxed font-medium">
                  TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE WILL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES; LOST PROFITS/REVENUE/GOODWILL/DATA; OR TRADING LOSSES. OUR TOTAL LIABILITY FOR ALL CLAIMS WILL NOT EXCEED THE AMOUNTS YOU PAID US FOR THE SERVICE IN THE 6 MONTHS BEFORE THE EVENT GIVING RISE TO LIABILITY. SOME JURISDICTIONS LIMIT SUCH EXCLUSIONS; IN THOSE, WE LIMIT LIABILITY TO THE MINIMUM EXTENT PERMITTED. NOTHING LIMITS LIABILITY FOR WILLFUL MISCONDUCT OR FRAUD.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">17) Indemnification</h2>
                <p className="text-gray-600 leading-relaxed">
                  You will defend, indemnify, and hold harmless Company and its affiliates, officers, directors, employees, and agents from claims and expenses (including reasonable attorneys' fees) arising from your use of the Service, your content, your breach of these Terms, or violation of law/third-party rights.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">18) Term; termination</h2>
                <p className="text-gray-600 leading-relaxed">
                  We may suspend or terminate access at any time to protect users or the Service, or for material violations. You may stop using the Service at any time. Sections that by nature should survive (ownership, disclaimers, limits, indemnity, disputes) survive termination.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">19) Changes</h2>
                <p className="text-gray-600 leading-relaxed">
                  We may change the Service or these Terms. If changes are material, we will notify you (e.g., email or in-app). Continued use after the effective date means acceptance.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">20) Governing law; venue</h2>
                <p className="text-gray-600 leading-relaxed">
                  These Terms are governed by the laws of Delaware, USA, without regard to conflicts rules. Subject to the arbitration section, courts located in Wilmington, Delaware have exclusive jurisdiction.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">21) Disputes; binding arbitration; class waiver</h2>
                <div className="text-gray-600 leading-relaxed space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Informal resolution first.</h3>
                    <p>Email legal@tradequest.tech; we'll try to resolve within 30 days.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Arbitration.</h3>
                    <p>Except for small-claims matters or injunctive relief, disputes will be resolved by binding arbitration administered by the American Arbitration Association (AAA) under its rules. Seat: Wilmington, Delaware. Language: English.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Class waiver.</h3>
                    <p>Disputes are on an individual basis only; no class or representative actions.</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Opt-out.</h3>
                    <p>You may opt out of arbitration/class waiver within 30 days of account creation by emailing legal@tradequest.tech with subject "Arbitration Opt-Out."</p>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">22) Notices; contact</h2>
                <p className="text-gray-600 leading-relaxed mb-3">
                  We may send notices electronically to your registered email or in-app. Legal notices to us must be sent to:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700">
                    <strong>Tradequest Technologies Inc. (d/b/a TradeQuest)</strong><br/>
                    1007 N Orange St, 4th Floor, Suite #4242<br/>
                    Wilmington, Delaware 19801, United States<br/>
                    <strong>Email:</strong> legal@tradequest.tech
                  </p>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">23) Miscellaneous</h2>
                <p className="text-gray-600 leading-relaxed">
                  Entire agreement (these Terms + Privacy Policy); severability; no waiver; assignment (you may not assign without consent; we may assign); force majeure; headings are for convenience only.
                </p>
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
