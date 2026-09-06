import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserRole, AuthUserInfo } from '../types';
import { authService } from '../services/api';

// Slim user type for auth context (no mock avatar/department required)
export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar: string;
  title: string;
  department: string;
  customerId?: string;
}

const DEFAULT_USER: AppUser = {
  id: '',
  name: '',
  email: '',
  role: 'SALES_REP',
  avatar: '',
  title: '',
  department: '',
};

interface AppContextType {
  // Authentication
  isAuthenticated: boolean;
  accessToken: string | null;
  currentUser: AppUser;
  setCurrentUser: (user: AppUser) => void;
  setUserRole: (role: UserRole) => void;
  setAuthSession: (token: string, user?: AuthUserInfo) => void;
  logout: () => Promise<void>;

  // UI Navigation
  currentPage: string;
  setCurrentPage: (page: string) => void;
  selectedQuoteId: string;
  setSelectedQuoteId: (id: string) => void;

  // Notifications
  notification: { message: string; type: 'success' | 'warning' | 'info' | 'error' } | null;
  showNotification: (message: string, type?: 'success' | 'warning' | 'info' | 'error') => void;

  // Quick test flow guide
  isGuideOpen: boolean;
  setIsGuideOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : fallback;
  } catch {
    return fallback;
  }
}

function saveToStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore storage errors
  }
}

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => authService.isAuthenticated());
  const [accessToken, setAccessToken] = useState<string | null>(() => authService.getAccessToken());
  const [currentUser, setCurrentUser] = useState<AppUser>(() => loadFromStorage('dealflow_user', DEFAULT_USER));

  // UI State
  const [currentPage, setCurrentPage] = useState<string>(() => loadFromStorage('dealflow_page', 'login'));
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>(() => loadFromStorage('dealflow_quote_id', ''));
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'warning' | 'info' | 'error' } | null>(null);
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);

  // Attempt silent session restore on mount via HttpOnly cookie
  useEffect(() => {
    let isMounted = true;
    const restoreSession = async () => {
      try {
        const res = await authService.refresh();
        if (res.access_token && isMounted) {
          authService.setAccessToken(res.access_token);
          setAccessToken(res.access_token);
          setIsAuthenticated(true);
          const me = await authService.getMe();
          if (me && isMounted) {
            setCurrentUser(prev => ({
              ...prev,
              id: me.id || prev.id,
              name: me.name || prev.name,
              email: me.email || prev.email,
              role: (me.role ? (String(me.role).toUpperCase() as UserRole) : prev.role),
              customerId: (me.customer_id || me.customerId) ?? prev.customerId,
            }));
          }
        }
      } catch {
        if (isMounted) {
          setIsAuthenticated(false);
          setAccessToken(null);
        }
      }
    };

    restoreSession();
    return () => { isMounted = false; };
  }, []);

  // Persist to localStorage
  useEffect(() => { saveToStorage('dealflow_user', currentUser); }, [currentUser]);
  useEffect(() => { saveToStorage('dealflow_page', currentPage); }, [currentPage]);
  useEffect(() => { saveToStorage('dealflow_quote_id', selectedQuoteId); }, [selectedQuoteId]);

  const setUserRole = (role: UserRole) => {
    setCurrentUser(prev => ({ ...prev, role }));
  };

  const showNotification = (message: string, type: 'success' | 'warning' | 'info' | 'error' = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4500);
  };

  const setAuthSession = (token: string, userInfo?: AuthUserInfo) => {
    authService.setAccessToken(token);
    setAccessToken(token);
    setIsAuthenticated(true);
    if (userInfo) {
      setCurrentUser(prev => ({
        ...prev,
        id: userInfo.id || prev.id,
        name: userInfo.name || userInfo.email.split('@')[0],
        email: userInfo.email,
        role: (userInfo.role ? (String(userInfo.role).toUpperCase() as UserRole) : prev.role || 'SALES_REP') as UserRole,
        title: userInfo.title || prev.title,
        department: userInfo.department || prev.department,
        customerId: (userInfo.customer_id || userInfo.customerId) ?? prev.customerId,
      }));
    }
  };

  const logout = async () => {
    await authService.logout();
    setAccessToken(null);
    setIsAuthenticated(false);
    setCurrentUser(DEFAULT_USER);
    setCurrentPage('login');
    showNotification('You have been signed out.', 'info');
  };

  return (
    <AppContext.Provider value={{
      isAuthenticated,
      accessToken,
      currentUser,
      setCurrentUser,
      setUserRole,
      setAuthSession,
      logout,
      currentPage,
      setCurrentPage,
      selectedQuoteId,
      setSelectedQuoteId,
      notification,
      showNotification,
      isGuideOpen,
      setIsGuideOpen,
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
