'use client'

import { useState } from 'react'
import Navigation from '@/components/Navigation'
import FileUploader from '@/components/FileUploader'
import ReportViewer from '@/components/ReportViewer'
import Dashboard from '@/components/Dashboard'
import PricingPlans from '@/components/PricingPlans'
import LoginForm from '@/components/LoginForm'
import { useAuth } from '@/hooks/useAuth'

export default function Home() {
  const [currentView, setCurrentView] = useState('home') // 'home', 'dashboard', 'pricing', 'login'
  const [currentStep, setCurrentStep] = useState('upload') // 'upload', 'processing', 'results'
  const [activeReport, setActiveReport] = useState(null)
  const { user, login, logout, credits, deductCredit } = useAuth()

  const handleViewChange = (view) => {
    setCurrentView(view)
    if (view === 'home') {
      setCurrentStep('upload')
      setActiveReport(null)
    }
  }

  const handleReportGenerated = (report) => {
    setActiveReport(report)
    setCurrentStep('results')
    deductCredit()
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'login':
        return <LoginForm onLogin={login} onViewChange={handleViewChange} />
      
      case 'pricing':
        return <PricingPlans />
      
      case 'dashboard':
        return (
          <Dashboard 
            user={user}
            credits={credits}
            onViewChange={handleViewChange}
            onReportSelect={(report) => {
              setActiveReport(report)
              setCurrentStep('results')
              setCurrentView('home')
            }}
          />
        )
      
      case 'home':
      default:
        if (currentStep === 'results' && activeReport) {
          return (
            <ReportViewer
              report={activeReport}
              user={user}
              onNewComparison={() => {
                setCurrentStep('upload')
                setActiveReport(null)
              }}
              onUpgrade={() => setCurrentView('pricing')}
            />
          )
        }
        return (
          <FileUploader
            user={user}
            credits={credits}
            currentStep={currentStep}
            onStepChange={setCurrentStep}
            onReportGenerated={handleReportGenerated}
            onLogin={() => setCurrentView('login')}
          />
        )
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation
        currentView={currentView}
        onViewChange={handleViewChange}
        user={user}
        credits={credits}
        onLogout={logout}
      />
      {renderCurrentView()}
    </div>
  )
}
