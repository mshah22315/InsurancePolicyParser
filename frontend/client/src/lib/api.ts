// API client configuration for backend communication
const API_BASE_URL = 'http://localhost:5001'; // Use backend directly to avoid proxy issues

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        credentials: 'include',
        ...options,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('/api/dashboard/stats');
  }

  // Policies
  async getPolicies(limit = 50, offset = 0) {
    return this.request(`/api/policies?limit=${limit}&offset=${offset}`);
  }

  async getPolicyById(id: number) {
    return this.request(`/api/policies/${id}`);
  }

  async searchPolicies(query: string) {
    return this.request(`/api/policies/search?q=${encodeURIComponent(query)}`);
  }

  async createPolicy(policyData: any) {
    return this.request('/api/policies', {
      method: 'POST',
      body: JSON.stringify(policyData),
    });
  }

  async updatePolicy(id: number, policyData: any) {
    return this.request(`/api/policies/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(policyData),
    });
  }

  // Policy upload
  async uploadPolicy(file: File) {
    const formData = new FormData();
    formData.append('document', file);

    try {
      const response = await fetch(`${this.baseUrl}/api/policies/upload`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Property features
  async getPolicyFeatures(policyId: number) {
    return this.request(`/api/policies/${policyId}/features`);
  }

  // Processing tasks
  async getProcessingTasks(limit = 50) {
    return this.request(`/api/processing-tasks?limit=${limit}`);
  }

  async getProcessingTask(taskId: string) {
    return this.request(`/api/processing-tasks/${taskId}`);
  }



  // Policy queries
  async queryPolicy(policyId: string, query: string) {
    return this.request('/api/policies/query', {
      method: 'POST',
      body: JSON.stringify({ policyId, query }),
    });
  }

  // Policy context updates
  async updatePolicyContext(policyId: string, data: { installationDate?: string; renewalDate?: string; propertyFeatures: string[] }) {
    return this.request(`/api/policies/${policyId}/context`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL); 