import React from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../../icons/logo.png';
import './Header.css';

const Header = () => {
  const navigate = useNavigate();

  return (
    <div className="header-container">
      <img
        src={logo}
        alt="Logo"
        className="logo-image"
        onClick={() => navigate('/')}
        style={{ cursor: 'pointer' }}
      />
      <div className="powered-by">
        <span className="powered-by-label">Powered by</span>
        <span className="badge badge-aws">AWS</span>
        <span className="badge badge-mongodb">MongoDB Atlas</span>
        <span className="badge badge-voyage">Voyage AI</span>
      </div>
    </div>
  );
};

export default Header;
