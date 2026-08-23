import React from 'react';
import { SignupPage } from './AuthPages';
import { useNavigate } from 'react-router-dom';

const SignupWrapper: React.FC = () => {
  const navigate = useNavigate();
  return <SignupPage onSwitchToLogin={() => navigate('/login')} />;
};

export default SignupWrapper;
