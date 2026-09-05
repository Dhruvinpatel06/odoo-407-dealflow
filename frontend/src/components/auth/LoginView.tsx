import React, { useState } from 'react';
import { 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  ArrowRight,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { authService, AuthError } from '../../services/authService';

export const LoginView: React.FC = () => {
  const { setCurrentPage, setAuthSession, showNotification } = useApp();
  
  const [emailInput, setEmailInput] = useState<string>('');
  const [passwordInput, setPasswordInput] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    const trimmedEmail = emailInput.trim();

    // Frontend validation
    if (!trimmedEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }

    if (!passwordInput) {
      setErrorMessage('Please enter your password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await authService.login({
        email: trimmedEmail,
        password: passwordInput,
      });

      // Query current user if not provided in login response
      let authUser = response.user;
      if (!authUser) {
        const me = await authService.getMe();
        if (me) {
          authUser = me;
        }
      }

      // Establish authenticated application state
      setAuthSession(response.access_token, authUser);
      showNotification('Signed in successfully', 'success');

      // Redirect to authenticated application entry point
      if (authUser?.role === 'CUSTOMER_PORTAL' || authUser?.role === 'CUSTOMER') {
        setCurrentPage('portal');
      } else {
        setCurrentPage('dashboard');
      }
    } catch (err: unknown) {
      if (err instanceof AuthError) {
        setErrorMessage(err.message);
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('An unexpected error occurred during sign in. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-4 select-none">
      {/* Brand Header */}
      <div className="flex flex-col items-center text-center mb-6">
        <div className="w-12 h-12 bg-[#2563EB] rounded-2xl flex items-center justify-center shadow-xs mb-3.5">
          <div className="w-4 h-4 border-2 border-white rotate-45 rounded-2xs"></div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
          DealFlow<span className="text-[#2563EB]">360</span>
        </h1>
        <p className="text-xs text-slate-500 font-normal mt-1">
          Intelligent Sales Operations Platform
        </p>
      </div>

      {/* Auth Card */}
      <div className="w-full max-w-[430px] bg-white rounded-2xl border border-slate-200/80 shadow-xs p-8">
        {/* Error / Validation Message */}
        {errorMessage && (
          <div 
            role="alert"
            className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600" />
            <span className="leading-relaxed">{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSignIn} className="space-y-4">
          {/* Email Field */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1.5">
              Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
              <input
                type="email"
                value={emailInput}
                onChange={(e) => {
                  setEmailInput(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                disabled={isLoading}
                placeholder="name@dealflow360.io"
                className="w-full bg-white border border-slate-200 rounded-lg pl-10 pr-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={passwordInput}
                onChange={(e) => {
                  setPasswordInput(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                disabled={isLoading}
                placeholder="••••••••"
                className="w-full bg-white border border-slate-200 rounded-lg pl-10 pr-10 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 transition p-0.5 cursor-pointer disabled:cursor-not-allowed"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-[#2563EB] hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-2 transition-colors shadow-xs cursor-pointer disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In to DealFlow360</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

