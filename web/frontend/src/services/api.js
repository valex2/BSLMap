import axios from 'axios';

// Use the full URL in development to avoid CORS issues
const API_BASE_URL = 'http://localhost:8000/api';

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API Error Response:', {
        status: error.response.status,
        data: error.response.data,
        headers: error.response.headers,
      });
      return Promise.reject({
        message: error.response.data?.message || 'An error occurred',
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API Request Error:', error.request);
      return Promise.reject({
        message: 'No response received from server',
        request: error.request,
      });
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Error:', error.message);
      return Promise.reject({
        message: error.message || 'An error occurred',
      });
    }
  }
);

/**
 * Get all labs with optional filters
 * @param {Object} filters - Filter criteria
 * @returns {Promise<Array>} - Array of lab features
 */
export const getLabs = async (filters = {}) => {
  try {
    const response = await api.get('/labs', { params: filters });
    return response.data;
  } catch (error) {
    console.error('Error fetching labs:', error);
    throw error;
  }
};

/**
 * Get a single lab by ID
 * @param {string} id - Lab ID
 * @returns {Promise<Object>} - Lab feature
 */
export const getLabById = async (id) => {
  if (!id) return null;
  
  try {
    const response = await api.get(`/labs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching lab ${id}:`, error);
    throw error;
  }
};

/**
 * Get all unique pathogens
 * @returns {Promise<Array>} - Array of pathogen names
 */
export const getPathogens = async () => {
  try {
    const response = await api.get('/pathogens');
    return response.data;
  } catch (error) {
    console.error('Error fetching pathogens:', error);
    throw error;
  }
};

/**
 * Get all unique research types
 * @returns {Promise<Array>} - Array of research types
 */
export const getResearchTypes = async () => {
  try {
    const response = await api.get('/research-types');
    return response.data;
  } catch (error) {
    console.error('Error fetching research types:', error);
    throw error;
  }
};

/**
 * Search labs by query string
 * @param {string} query - Search query
 * @returns {Promise<Array>} - Array of matching labs
 */
export const searchLabs = async (query) => {
  try {
    const response = await api.get('/search', { params: { q: query } });
    return response.data;
  } catch (error) {
    console.error('Error searching labs:', error);
    throw error;
  }
};

export default {
  getLabs,
  getLabById,
  getPathogens,
  getResearchTypes,
  searchLabs,
};
