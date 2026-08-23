import React from 'react';
import { LoginPage } from './AuthPages';
import { useNavigate } from 'react-router-dom';

const LoginWrapper: React.FC = () => {
  const navigate = useNavigate();
  return <LoginPage onSwitchToSignup={() => navigate('/signup')} />;
};

export default LoginWrapper;
