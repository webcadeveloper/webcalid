import Cookies from 'js-cookie';

export const setCookie = (name, value, options = {}) => {
  const defaultOptions = {
    path: '/',
    sameSite: 'Lax',
    secure: process.env.NODE_ENV === 'production',
    domain: window.location.hostname
  };

  const mergedOptions = { ...defaultOptions, ...options };

  try {
    Cookies.set(name, value, mergedOptions);
  } catch (error) {
    console.error(`Error setting cookie ${name}:`, error);
  }
};

export const getCookie = (name) => {
  try {
    return Cookies.get(name);
  } catch (error) {
    console.error(`Error getting cookie ${name}:`, error);
    return null;
  }
};

export const removeCookie = (name) => {
  try {
    Cookies.remove(name, { path: '/', domain: window.location.hostname });
  } catch (error) {
    console.error(`Error removing cookie ${name}:`, error);
  }
};

export const handleCookies = () => {
  // Set the __tld__ cookie with proper options
  setCookie('__tld__', 'example_value', {
    sameSite: 'Lax',
    secure: true,
    domain: window.location.hostname
  });
};

// Run the handleCookies function when the script is loaded
if (typeof window !== 'undefined') {
  handleCookies();
}

