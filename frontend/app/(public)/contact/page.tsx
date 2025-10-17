import Link from 'next/link';
import PublicHeader from "@/components/layout/PublicHeader";
import PublicFooter from "@/components/layout/PublicFooter";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-gray-900">
      <PublicHeader currentPage="contact" />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-6">
            Get in Touch
          </h1>
          <p className="text-xl text-gray-400">
            Have questions? We're here to help.
          </p>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-md rounded-2xl border border-gray-700 p-12">
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
          <div className="grid md:grid-cols-3 gap-8 pt-12 border-t border-gray-700">
            <div className="text-center">
              <div className="text-brand-bright-yellow font-semibold mb-2">Support</div>
              <p className="text-gray-400 text-sm">
                Technical support and account assistance
              </p>
            </div>
            <div className="text-center">
              <div className="text-brand-bright-yellow font-semibold mb-2">Sales</div>
              <p className="text-gray-400 text-sm">
                Questions about plans and features
              </p>
            </div>
            <div className="text-center">
              <div className="text-brand-bright-yellow font-semibold mb-2">Feedback</div>
              <p className="text-gray-400 text-sm">
                Share your ideas and suggestions
              </p>
            </div>
          </div>

          {/* Response Time */}
          <div className="mt-12 p-6 bg-gray-800/50 rounded-xl border border-gray-700 text-center">
            <p className="text-gray-300">
              <span className="text-brand-bright-yellow font-semibold">Average response time:</span> Within 24 hours
            </p>
          </div>
        </div>

      </main>

      <PublicFooter />
    </div>
  );
}

