/**
 * Authentication Service for Meeting Bot Dashboard
 * 
 * Handles user authentication with Supabase Auth
 */

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  session: {
    access_token: string;
    refresh_token: string;
    expires_at: number;
  };
}

export interface SignUpRequest {
  email: string;
  password: string;
}

export interface SignInRequest {
  email: string;
  password: string;
}

const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');

class AuthService {
  private getStoredToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  private setStoredToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  removeStoredToken(): void {
    localStorage.removeItem('auth_token');
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Sign up a new user
  async signUp(request: SignUpRequest): Promise<AuthResponse> {
    const response = await this.makeRequest<AuthResponse>('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify(request),
    });

    if (response.session?.access_token) {
      this.setStoredToken(response.session.access_token);
    }

    return response;
  }

  // Sign in an existing user
  async signIn(request: SignInRequest): Promise<AuthResponse> {
    const response = await this.makeRequest<AuthResponse>('/api/v1/auth/signin', {
      method: 'POST',
      body: JSON.stringify(request),
    });

    if (response.session?.access_token) {
      this.setStoredToken(response.session.access_token);
    }

    return response;
  }

  // Sign out the current user
  async signOut(): Promise<void> {
    try {
      const token = this.getStoredToken();
      if (token) {
        await this.makeRequest('/api/v1/auth/signout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Sign out error:', error);
    } finally {
      this.removeStoredToken();
    }
  }

  // Get current user info
  async getCurrentUser(): Promise<User | null> {
    try {
      const token = this.getStoredToken();
      if (!token) return null;

      const response = await this.makeRequest<User>('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      return response;
    } catch (error) {
      console.error('Get current user error:', error);
      this.removeStoredToken();
      return null;
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getStoredToken();
  }

  // Get token for API requests
  getToken(): string | null {
    return this.getStoredToken();
  }
}

// Create singleton instance
const authService = new AuthService();

export default authService;
