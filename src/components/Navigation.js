'use client'

import { useState } from 'react'
import { FileText, User, CreditCard, Menu, X, LogOut, Settings } from 'lucide-react'

export default function Navigation({ 
  currentView, 
  onViewChange, 
  user, 
  credits, 
  onLogout 
}) {
  const [showMobileMenu, setShowMobileMenu] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)

  const navLinks = [
    { id: 'home', label: 'Compare', show: true },
    { id: 'dashboard', label: 'Dashboard', show: !!user },
    { id: 'pricing', label: 'Pricing', show: true },
  ]

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center cursor-pointer" onClick={() => onViewChange('home')}>
              <FileText className="w-8 h-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">ClauseCompare</span>
            </div>
            
            {/* Desktop Navigation */}
            <div className="hidden md:ml-10 md:flex space-x-8">
              {navLinks.map((link) => (
                link.show && (
                  <button
                    key={link.id}
                    onClick={() => onViewChange(link.id)}
                    className={`${
                      currentView === link.id 
                        ? 'text-blue-600 border-blue-600' 
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors`}
                  >
                    {link.label}
                  </button>
                )
              ))}
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center">
            {user ? (
              <div className="flex items-center space-x-4">
                {/* Credits display */}
                <div className="hidden sm:flex items-center space-x-2 text-sm">
                  <CreditCard className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{credits} credits</span>
                </div>
                
                {/* User menu */}
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <User className="w-5 h-5" />
                    <span className="hidden md:block">{user.name || user.email}</span>
                  </button>
                  
                  {/* User dropdown */}
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 border border-gray-200">
                      <div className="px-4 py-2 text-xs text-gray-500 border-b border-gray-100">
                        {user.email}
                      </div>
                      <button
                        onClick={() => {
                          onViewChange('dashboard')
                          setShowUserMenu(false)
                        }}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                      >
                        <User className="w-4 h-4 mr-3" />
                        Dashboard
                      </button>
                      <button
                        onClick={() => {
                          onViewChange('pricing')
                          setShowUserMenu(false)
                        }}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                      >
                        <CreditCard className="w-4 h-4 mr-3" />
                        Billing
                      </button>
                      <button
                        onClick={() => {
                          onLogout()
                          setShowUserMenu(false)
                        }}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left border-t border-gray-100"
                      >
                        <LogOut className="w-4 h-4 mr-3" />
                        Sign out
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => onViewChange('login')}
                  className="text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => onViewChange('login')}
                  className="btn-primary"
                >
                  Get Started
                </button>
              </div>
            )}

            {/* Mobile menu button */}
            <div className="md:hidden ml-4">
              <button
                onClick={() => setShowMobileMenu(!showMobileMenu)}
                className="text-gray-500 hover:text-gray-700 p-2"
              >
                {showMobileMenu ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {showMobileMenu && (
          <div className="md:hidden border-t border-gray-200 py-3">
            <div className="space-y-1">
              {navLinks.map((link) => (
                link.show && (
                  <button
                    key={link.id}
                    onClick={() => {
                      onViewChange(link.id)
                      setShowMobileMenu(false)
                    }}
                    className={`${
                      currentView === link.id ? 'text-blue-600 bg-blue-50' : 'text-gray-600'
                    } block px-3 py-2 text-base font-medium w-full text-left hover:text-gray-900 hover:bg-gray-50 transition-colors`}
                  >
                    {link.label}
                  </button>
                )
              ))}
              
              {user && (
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="px-3 py-2 text-sm text-gray-500">
                    {credits} credits remaining
                  </div>
                  <button
                    onClick={() => {
                      onLogout()
                      setShowMobileMenu(false)
                    }}
                    className="block px-3 py-2 text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 w-full text-left transition-colors"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
              }
