import Link from 'next/link';

export default function RiskDisclaimerPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-teal via-brand-dark-teal to-gray-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link href="/">
              <img
                src="/images/logos/Transparent/TradeQuest [Colored] [Rectangle].png"
                alt="TradeQuest"
                className="h-10 w-auto"
              />
            </Link>
            <Link
              href="/auth"
              className="bg-white text-brand-dark-teal px-6 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 md:p-12">
          <h1 className="text-4xl font-bold text-white mb-8">Risk Disclaimer</h1>
          
          <div className="prose prose-invert prose-lg max-w-none space-y-6 text-gray-200">
            <p className="text-sm text-gray-400">
              Last Updated: October 3, 2025
            </p>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Trading Risk Warning</h2>
              <p>
                Trading stocks, options, futures, forex, and other financial instruments involves substantial risk of loss and is not suitable for every investor. The valuation of financial instruments may fluctuate, and, as a result, clients may lose more than their original investment. Past performance is not necessarily indicative of future results.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">No Investment Advice</h2>
              <p>
                TradeQuest is a trading journal, analytics, and educational platform. We do not provide investment advice, financial advice, trading advice, or any other sort of advice. All content on this platform, including but not limited to AI-generated insights, analytics, and educational materials, is for informational and educational purposes only.
              </p>
              <p>
                You alone are solely responsible for determining whether any investment, security, or strategy is appropriate for you based on your investment objectives, financial situation, and risk tolerance. You should consult with licensed financial advisors, accountants, and/or attorneys before making any financial decisions.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Performance Results</h2>
              <p>
                Any performance results, statistics, or backtesting data displayed on the platform are hypothetical in nature and do not represent actual trading results. Hypothetical performance results have inherent limitations, including but not limited to:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>They do not reflect actual trading or the impact of non-economic factors such as liquidity constraints, execution delays, and market impact.</li>
                <li>Backtested results are calculated with the benefit of hindsight and do not represent actual performance.</li>
                <li>They may not reflect the impact of material economic and market factors on decision-making if actual funds were being managed.</li>
                <li>Simulated trading programs are designed with the benefit of hindsight and may not reflect future market conditions.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">AI-Generated Content</h2>
              <p>
                TradeQuest utilizes artificial intelligence and machine learning technologies to provide insights, analysis, and educational content. AI-generated content may contain errors, inaccuracies, or outdated information. All AI-generated insights should be independently verified and should not be relied upon as the sole basis for any trading decision.
              </p>
              <p>
                The use of AI technology does not guarantee accurate predictions, profitable trading outcomes, or risk-free investments. Market conditions change rapidly and AI models may not adapt quickly enough to reflect current market realities.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Paper Trading and Simulations</h2>
              <p>
                Paper trading features allow users to practice trading strategies without risking real money. However, paper trading results do not account for:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Slippage - the difference between expected and actual execution prices</li>
                <li>Market impact - how your orders would affect market prices</li>
                <li>Liquidity constraints - inability to enter or exit positions at desired prices</li>
                <li>Emotional factors - the psychological impact of risking real capital</li>
                <li>Commission costs, fees, and taxes</li>
              </ul>
              <p>
                Success in paper trading does not guarantee success in real trading with actual capital.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Market Data and Accuracy</h2>
              <p>
                While we strive to provide accurate and timely market data, TradeQuest cannot guarantee the accuracy, completeness, or timeliness of any market data, quotes, charts, or other information provided through the platform. Market data may be delayed, and technical issues may result in interruptions or inaccuracies.
              </p>
              <p>
                Users should not rely solely on data provided by TradeQuest for time-sensitive trading decisions and should verify all data through official sources.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Platform Availability</h2>
              <p>
                While we maintain high availability standards, TradeQuest does not guarantee uninterrupted access to the platform. Technical issues, maintenance, or other factors may result in temporary unavailability. We are not liable for any losses resulting from inability to access the platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">No Guaranteed Results</h2>
              <p>
                TradeQuest makes no representations or warranties regarding the likelihood of any particular trading outcome. There are no guarantees of profit, and trading can result in substantial losses. Users acknowledge that:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>They may lose all or more than their invested capital</li>
                <li>Past performance does not predict future results</li>
                <li>No trading system or methodology has a guaranteed outcome</li>
                <li>Market conditions can change rapidly and unpredictably</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Regulatory Compliance</h2>
              <p>
                It is your responsibility to comply with all applicable laws and regulations in your jurisdiction, including but not limited to securities laws, tax laws, and regulations governing financial trading. TradeQuest is not responsible for ensuring your compliance with applicable laws.
              </p>
              <p>
                Different jurisdictions have different regulations regarding trading and the use of trading tools. Ensure that your use of TradeQuest complies with all applicable regulations in your location.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Third-Party Integrations</h2>
              <p>
                TradeQuest may integrate with third-party services, brokers, or data providers. We are not responsible for the actions, services, or failures of any third party. Any transactions conducted through third-party integrations are solely between you and that third party.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Limitation of Liability</h2>
              <p>
                To the maximum extent permitted by law, TradeQuest, its officers, directors, employees, and affiliates shall not be liable for any direct, indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, revenue, data, or use, arising out of or related to:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Your use of or inability to use the platform</li>
                <li>Any trading decisions made based on platform features or content</li>
                <li>Errors, inaccuracies, or omissions in platform data or content</li>
                <li>Unauthorized access to your account or data</li>
                <li>Platform downtime or technical failures</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Professional Advice Recommended</h2>
              <p>
                Before making any investment decisions, you should seek advice from independent financial, legal, and tax advisors. TradeQuest strongly recommends that you:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Understand the risks involved in trading</li>
                <li>Only trade with capital you can afford to lose</li>
                <li>Develop a comprehensive risk management strategy</li>
                <li>Continuously educate yourself about market dynamics</li>
                <li>Never invest based solely on others' recommendations or AI-generated insights</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mt-8 mb-4">Acknowledgment</h2>
              <p>
                By using TradeQuest, you acknowledge that you have read, understood, and agree to this Risk Disclaimer. You accept full responsibility for your trading decisions and agree to hold TradeQuest harmless from any losses or damages resulting from your use of the platform.
              </p>
              <p className="font-semibold text-white mt-4">
                TRADING INVOLVES SUBSTANTIAL RISK. ONLY RISK CAPITAL THAT YOU CAN AFFORD TO LOSE.
              </p>
            </section>

            <section className="mt-12 pt-8 border-t border-white/10">
              <p className="text-sm text-gray-400">
                For questions about this Risk Disclaimer, please contact us at{' '}
                <a href="mailto:info@tradequest.tech" className="text-brand-teal hover:text-brand-light-teal">
                  info@tradequest.tech
                </a>
              </p>
            </section>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center mt-12">
          <Link
            href="/"
            className="inline-flex items-center text-gray-300 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
}

