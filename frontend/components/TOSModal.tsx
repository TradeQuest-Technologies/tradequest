"use client";

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface TOSModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function TOSModal({ isOpen, onClose }: TOSModalProps) {
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
                    Terms of Service
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
                        These Terms of Service ("Terms") are a binding agreement between Tradequest Technologies Inc., 
                        a Delaware corporation, d/b/a TradeQuest ("Company," "we," "us," or "our") and you ("you" or "User"). 
                        By accessing or using our websites, apps, APIs, or related services (collectively, the "Service"), 
                        you agree to these Terms. If you do not agree, do not use the Service.
                      </p>

                      <div className="space-y-4">
                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">1) What we do (educational software; not a broker)</h4>
                          <p className="text-sm text-gray-700">
                            We provide subscription software for trade journaling, analytics, backtesting, and AI-assisted reviews 
                            via read-only broker integrations (the "Platform"). We do not provide investment, legal, tax, accounting, 
                            or other professional advice, and we are not a broker-dealer, investment adviser, exchange, ATS, or money transmitter. 
                            The Service is educational and for information only.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">2) Eligibility; accounts; security</h4>
                          <div className="space-y-2">
                            <div>
                              <h5 className="font-medium text-gray-900">Age.</h5>
                              <p className="text-sm text-gray-700">
                                You must be 16+ to use the Service. If you are under 18, you may use the Service only with 
                                parent/guardian consent and where permitted by law.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Account security.</h5>
                              <p className="text-sm text-gray-700">
                                You are responsible for maintaining the confidentiality of your credentials, enabling 2FA, 
                                and all activity under your account. Notify us promptly of unauthorized use.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Accuracy.</h5>
                              <p className="text-sm text-gray-700">
                                You agree your registration and profile information is accurate and kept updated.
                              </p>
                            </div>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">3) Subscriptions; billing; refunds</h4>
                          <div className="space-y-2">
                            <div>
                              <h5 className="font-medium text-gray-900">Charge timing.</h5>
                              <p className="text-sm text-gray-700">
                                Paid plans are billed at checkout (monthly or annual) in USD via our payment processor (e.g., Stripe). 
                                Taxes may apply.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Auto-renewal & cancellation.</h5>
                              <p className="text-sm text-gray-700">
                                Subscriptions renew until canceled in your Account. Cancellation stops future renewals; it doesn't refund time already used unless our refund policy applies.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Refund policy (baseline).</h5>
                              <p className="text-sm text-gray-700">
                                First-time purchases are refundable within 7 days upon request to support@tradequest.tech. 
                                Renewals are generally non-refundable except where required by law.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Price/features changes.</h5>
                              <p className="text-sm text-gray-700">
                                We may change prices or features prospectively; we'll notify you before changes affecting your next renewal.
                              </p>
                            </div>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">4) Strict "no advice" + risk disclosures</h4>
                          <div className="space-y-2">
                            <div>
                              <h5 className="font-medium text-gray-900">No advice or recommendations.</h5>
                              <p className="text-sm text-gray-700">
                                Content, analytics, and AI outputs are not investment advice or a solicitation to buy/sell any security, digital asset, or instrument.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">No guarantees.</h5>
                              <p className="text-sm text-gray-700">
                                Backtests and simulations are hypothetical and may differ materially from actual results. Past performance is not indicative of future results.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Your risk.</h5>
                              <p className="text-sm text-gray-700">
                                Trading involves risk, including total loss. You alone are responsible for your trades and outcomes.
                              </p>
                            </div>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">5) Broker connections; data sources</h4>
                          <div className="space-y-2">
                            <div>
                              <h5 className="font-medium text-gray-900">Read-only keys only.</h5>
                              <p className="text-sm text-gray-700">
                                Integrations require read-only API keys. Never grant withdrawal/transfer permissions. You are responsible for key management.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">Third parties.</h5>
                              <p className="text-sm text-gray-700">
                                Broker APIs, market data, and third-party services are outside our control and may be inaccurate, delayed, incomplete, or unavailable.
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-900">No execution.</h5>
                              <p className="text-sm text-gray-700">
                                We do not place, route, or execute orders.
                              </p>
                            </div>
                          </div>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">6) Acceptable use</h4>
                          <p className="text-sm text-gray-700">
                            You agree not to: (a) use the Service for unlawful purposes or market abuse; (b) violate third-party terms or IP rights; 
                            (c) scrape at scale or reverse engineer; (d) circumvent security or plan limits; (e) upload malware or unlawful content; 
                            (f) attempt to access others' accounts or data. We may suspend or terminate access for violations or to protect the Service and users.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">15) Disclaimers</h4>
                          <p className="text-sm text-gray-700 font-medium">
                            TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, OR STATUTORY (INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, ACCURACY, AVAILABILITY). WE DO NOT WARRANT RESULTS, ANALYTICS, OR AI OUTPUTS WILL BE ERROR-FREE OR UNINTERRUPTED.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">16) Limitation of liability</h4>
                          <p className="text-sm text-gray-700 font-medium">
                            TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE WILL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES; LOST PROFITS/REVENUE/GOODWILL/DATA; OR TRADING LOSSES. OUR TOTAL LIABILITY FOR ALL CLAIMS WILL NOT EXCEED THE AMOUNTS YOU PAID US FOR THE SERVICE IN THE 6 MONTHS BEFORE THE EVENT GIVING RISE TO LIABILITY. SOME JURISDICTIONS LIMIT SUCH EXCLUSIONS; IN THOSE, WE LIMIT LIABILITY TO THE MINIMUM EXTENT PERMITTED. NOTHING LIMITS LIABILITY FOR WILLFUL MISCONDUCT OR FRAUD.
                          </p>
                        </section>

                        <section>
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">22) Notices; contact</h4>
                          <div className="text-sm text-gray-700">
                            <p>We may send notices electronically to your registered email or in-app. Legal notices to us must be sent to:</p>
                            <div className="mt-2 p-3 bg-gray-50 rounded">
                              <p><strong>Tradequest Technologies Inc. (d/b/a TradeQuest)</strong></p>
                              <p>1007 N Orange St, 4th Floor, Suite #4242</p>
                              <p>Wilmington, Delaware 19801, United States</p>
                              <p><strong>Email:</strong> legal@tradequest.tech</p>
                            </div>
                          </div>
                        </section>

                        <div className="bg-blue-50 p-4 rounded-lg">
                          <p className="text-sm text-blue-800">
                            <strong>Note:</strong> This is a summary of key terms. The full Terms of Service contain additional important provisions 
                            including dispute resolution, governing law, and other legal terms. By using TradeQuest, you agree to be bound by 
                            the complete Terms of Service.
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
