import Link from 'next/link'

interface PublicFooterProps {
  className?: string
}

export default function PublicFooter({ className }: PublicFooterProps) {
  return (
    <footer className={`bg-black border-t border-gray-800 text-white py-16 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-8">
          <div>
            <img
              src="/images/logos/Transparent/TradeQuest%20%5BColored%5D%20%5BRectangle%5D.png"
              alt="TradeQuest"
              className="h-10 w-auto mb-4"
            />
            <p className="text-gray-400 leading-relaxed">
              The trading platform that focuses on education, discipline, and continuous improvement.
            </p>
          </div>
          <div>
            <h4 className="font-bold text-white mb-4">Product</h4>
            <ul className="space-y-3 text-gray-400">
              <li><Link href="/features" className="hover:text-brand-bright-yellow transition-colors">Features</Link></li>
              <li><Link href="/pricing" className="hover:text-brand-bright-yellow transition-colors">Pricing</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white mb-4">Company</h4>
            <ul className="space-y-3 text-gray-400">
              <li><Link href="/contact" className="hover:text-brand-bright-yellow transition-colors">Contact</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white mb-4">Legal</h4>
            <ul className="space-y-3 text-gray-400">
              <li><Link href="/terms" className="hover:text-brand-bright-yellow transition-colors">Terms of Service</Link></li>
              <li><Link href="/privacy" className="hover:text-brand-bright-yellow transition-colors">Privacy Policy</Link></li>
              <li><Link href="/risk-disclaimer" className="hover:text-brand-bright-yellow transition-colors">Risk Disclaimer</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 pt-8 text-center">
          <p className="text-gray-500">&copy; 2025 TradeQuest. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
