"use client";

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface PrivacyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function PrivacyModal({ isOpen, onClose }: PrivacyModalProps) {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                  <Dialog.Title as="h3" className="text-2xl font-bold text-gray-900">
                    Privacy Policy
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="rounded-md p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="max-h-96 overflow-y-auto p-6">
                    <div className="prose prose-sm max-w-none">
                      <p className="text-sm text-gray-600 mb-6">
                        <strong>Last updated:</strong> September 28, 2025
                      </p>

                      <p className="text-sm text-gray-700 mb-6">
                        Tradequest Technologies Inc., d/b/a "TradeQuest" ("TradeQuest," "we," "us," or "our") provides this Privacy Policy 
                        to explain how we collect, use, share, and protect information when you access our websites, apps, APIs, and related services (collectively, the "Service").
                      </p>

                      <p className="text-sm text-gray-700 mb-6">
                        If you do not agree with this Privacy Policy, please do not use the Service.
                      </p>

                      <div className="space-y-4">
                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">Who we are (controller):</h4>
                          <div className="text-sm text-gray-700">
                            <p><strong>Tradequest Technologies Inc. (d/b/a TradeQuest)</strong></p>
                            <p>1007 N Orange St, 4th Floor, Suite #4242, Wilmington, Delaware 19801, United States</p>
                            <p>Support: support@tradequest.tech • Privacy: privacy@tradequest.tech</p>
                            <p>Website: https://tradequest.tech</p>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">1) Scope</h4>
                          <p className="text-sm text-gray-700">
                            This Policy covers personal information we process when you use the Service or interact with us (e.g., support). It does not cover third-party websites, services, or practices that we do not control.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">2) Information we collect</h4>
                          <div className="space-y-3">
                            <div>
                              <h5 className="font-medium text-gray-900">A) You provide to us</h5>
                              <ul className="text-sm text-gray-700 list-disc list-inside space-y-1 ml-4">
                                <li><strong>Account & contact:</strong> email, alias, timezone, display preferences.</li>
                                <li><strong>Security:</strong> optional password, 2FA/TOTP setup (stored as hashed/secret values).</li>
                                <li><strong>Trading data:</strong> trade logs, notes, tags, uploaded files/screenshots, journal entries.</li>
                                <li><strong>Broker API keys (read-only):</strong> keys you provide to connect your broker/exchange. We instruct users to never grant withdrawal/transfer permissions. Keys are stored encrypted.</li>
                                <li><strong>Preferences:</strong> goals, risk rules, discipline settings, notification and AI/backtesting preferences.</li>
                                <li><strong>Support:</strong> messages and attachments you send to support@tradequest.tech.</li>
                              </ul>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">B) Automatically collected</h5>
                              <ul className="text-sm text-gray-700 list-disc list-inside space-y-1 ml-4">
                                <li><strong>Device/technical:</strong> IP address, browser/OS, device identifiers, language, referring/exit pages.</li>
                                <li><strong>Usage & events:</strong> pages viewed, features used, timestamps, error logs, job metrics (e.g., imports, backtests).</li>
                                <li><strong>Cookies & similar:</strong> essential session cookies, preference cookies, and (if enabled) privacy-centric analytics cookies. See "Cookies & Tracking" below.</li>
                              </ul>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">C) From third parties</h5>
                              <ul className="text-sm text-gray-700 list-disc list-inside space-y-1 ml-4">
                                <li><strong>Payments:</strong> limited transaction metadata from our payment processor (e.g., Stripe). We do not store full card numbers.</li>
                                <li><strong>Messaging:</strong> your Telegram user ID when you link alerts.</li>
                                <li><strong>Brokers/exchanges:</strong> fills/positions when you connect read-only keys.</li>
                              </ul>
                              <p className="text-sm text-gray-700 mt-2">
                                We do not intentionally collect special/sensitive categories of data (e.g., health, biometric). Please avoid uploading others' personal data without permission.
                              </p>
                            </div>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">3) How we use information</h4>
                          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                            <li><strong>Provide the Service:</strong> authenticate accounts, import and normalize broker data, journal/analytics/backtests, alerts, reports, account administration.</li>
                            <li><strong>Improve & secure:</strong> monitor performance, debug issues, detect/prevent abuse, develop features, maintain availability.</li>
                            <li><strong>Communicate:</strong> transactional emails (logins, receipts, alerts), service messages, responses to support.</li>
                            <li><strong>Marketing (optional):</strong> send product updates or promotions only if you opt in; unsubscribe anytime.</li>
                            <li><strong>Legal compliance & protection:</strong> enforce Terms, comply with law, and protect rights, property, and safety.</li>
                          </ul>
                          
                          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                            <h5 className="font-medium text-blue-900 mb-2">AI features</h5>
                            <p className="text-sm text-blue-800">
                              To deliver AI-powered analyses (e.g., trade context summaries), we may process relevant data (such as candles around a trade, trade logs) with an AI provider under contract. For quality improvement, we use anonymized telemetry only if you opt in. AI outputs may be inaccurate—use judgment.
                            </p>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">5) Sharing & disclosures</h4>
                          <p className="text-sm text-gray-700 mb-3">
                            We share personal information only as described below and with appropriate safeguards:
                          </p>
                          <div className="space-y-2">
                            <div>
                              <h5 className="font-medium text-gray-900">Service providers / subprocessors (on our behalf):</h5>
                              <ul className="text-sm text-gray-700 list-disc list-inside space-y-1 ml-4">
                                <li><strong>Payments:</strong> Stripe (billing and receipts).</li>
                                <li><strong>Email delivery:</strong> a reputable email service for login links/receipts/alerts.</li>
                                <li><strong>Error tracking & logging:</strong> a reputable provider to diagnose issues.</li>
                                <li><strong>Product analytics (privacy-centric):</strong> to understand feature usage at an aggregate level.</li>
                                <li><strong>AI processing:</strong> a hosted AI API provider to generate requested analyses.</li>
                                <li><strong>Messaging:</strong> Telegram Bot API (if you link).</li>
                                <li><strong>Hosting/infra & storage:</strong> US-based compute and storage providers.</li>
                              </ul>
                              <p className="text-sm text-gray-700 mt-2">These providers are bound by contracts limiting use of your data to providing services to us.</p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Legal/compliance:</h5>
                              <p className="text-sm text-gray-700">if required by law or in response to a lawful request, to protect our rights or users' safety, or to enforce our Terms.</p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Corporate transactions:</h5>
                              <p className="text-sm text-gray-700">in connection with merger, acquisition, financing, or sale of assets (we will continue to protect personal data and notify you of material changes).</p>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 mt-3 font-medium">
                            We do not "sell" or "share" personal information for cross-context behavioral advertising (as those terms are defined under US state privacy laws).
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">8) Your choices & controls</h4>
                          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                            <li><strong>Access & edits:</strong> manage most info in the app; contact privacy@tradequest.tech if you need help.</li>
                            <li><strong>Marketing emails:</strong> opt in/out in settings or via the unsubscribe link. Transactional emails (e.g., login links, receipts) are required.</li>
                            <li><strong>Cookies & Tracking:</strong> you can control cookies via your browser. Essential cookies are required for login/session.</li>
                            <li><strong>Telemetry for improvement:</strong> off by default; you may opt in or out at any time.</li>
                            <li><strong>Broker keys:</strong> you can revoke access at any time from Integrations; we will stop syncing and delete stored keys.</li>
                          </ul>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">11) Security</h4>
                          <p className="text-sm text-gray-700">
                            We use reasonable technical and organizational measures, including:
                          </p>
                          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1 mt-2">
                            <li>Encryption in transit (TLS) and at rest for sensitive fields (e.g., AES-GCM for broker keys).</li>
                            <li>httpOnly, secure cookies, CSRF protections, rate limiting, access controls, and audit logging.</li>
                            <li>Least-privilege access for staff and systems.</li>
                          </ul>
                          <p className="text-sm text-gray-700 mt-3">
                            No method is 100% secure. If we learn of a breach affecting your data, we will notify you without undue delay consistent with applicable law.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">12) Children's privacy</h4>
                          <p className="text-sm text-gray-700">
                            The Service is not intended for children under 16. If you believe we have collected data from a child under 16, contact privacy@tradequest.tech and we will delete it.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">15) Contact us</h4>
                          <div className="text-sm text-gray-700">
                            <p><strong>Tradequest Technologies Inc. (d/b/a TradeQuest)</strong></p>
                            <p>1007 N Orange St, 4th Floor, Suite #4242</p>
                            <p>Wilmington, Delaware 19801, United States</p>
                            <p>Support: support@tradequest.tech • Privacy: privacy@tradequest.tech</p>
                          </div>
                        </section>

                        <div className="bg-green-50 p-4 rounded-lg">
                          <p className="text-sm text-green-800">
                            <strong>Your privacy matters:</strong> We are committed to protecting your personal information and being transparent 
                            about our data practices. If you have any questions about this Privacy Policy, please contact us at privacy@tradequest.tech.
                          </p>
                        </div>
                      </div>
                  </div>
                </div>

                <div className="flex justify-end p-6 border-t border-gray-200">
                  <button
                    onClick={onClose}
                    className="px-6 py-2 bg-brand-dark-teal text-white rounded-lg hover:bg-brand-dark-teal/90 transition-colors"
                  >
                    I Understand
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
