import Link from 'next/link';

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-teal via-brand-dark-teal to-gray-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-2xl font-bold text-white">
              TradeQuest
            </Link>
            <nav className="hidden md:flex space-x-8">
              <Link href="/features" className="text-gray-200 hover:text-white">
                Features
              </Link>
              <Link href="/pricing" className="text-gray-200 hover:text-white">
                Pricing
              </Link>
              <Link href="/docs" className="text-gray-200 hover:text-white">
                Docs
              </Link>
              <Link href="/contact" className="text-white font-semibold">
                Contact
              </Link>
            </nav>
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
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-6">
            Get in Touch
          </h1>
          <p className="text-xl text-gray-300">
            Have questions? We're here to help.
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-12">
          {/* Email Contact */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand-teal/20 mb-6">
              <svg className="w-8 h-8 text-brand-teal" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Email Us</h2>
            <p className="text-gray-300 mb-6">
              Send us an email and we'll get back to you within 24 hours.
            </p>
            <a
              href="mailto:info@tradequest.tech"
              className="inline-flex items-center text-2xl font-semibold text-brand-teal hover:text-brand-light-teal transition-colors"
            >
              info@tradequest.tech
              <svg className="w-6 h-6 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </a>
          </div>

          {/* Additional Info */}
          <div className="grid md:grid-cols-3 gap-8 pt-12 border-t border-white/10">
            <div className="text-center">
              <div className="text-brand-teal font-semibold mb-2">Support</div>
              <p className="text-gray-300 text-sm">
                Technical support and account assistance
              </p>
            </div>
            <div className="text-center">
              <div className="text-brand-teal font-semibold mb-2">Sales</div>
              <p className="text-gray-300 text-sm">
                Questions about plans and features
              </p>
            </div>
            <div className="text-center">
              <div className="text-brand-teal font-semibold mb-2">Feedback</div>
              <p className="text-gray-300 text-sm">
                Share your ideas and suggestions
              </p>
            </div>
          </div>

          {/* Response Time */}
          <div className="mt-12 p-6 bg-white/5 rounded-xl border border-white/10 text-center">
            <p className="text-gray-300">
              <span className="text-brand-teal font-semibold">Average response time:</span> Within 24 hours
            </p>
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

