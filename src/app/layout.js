import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'ClauseCompare - AI-Powered Contract Analysis',
  description: 'Upload two contract versions and get instant risk analysis with negotiation guidance. Privacy-first, audit-ready reports in seconds.',
  keywords: 'contract comparison, legal analysis, AI contract review, contract risk assessment',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div id="root">{children}</div>
      </body>
    </html>
  )
}
