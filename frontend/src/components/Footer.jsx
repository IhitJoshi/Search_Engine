import React from "react";

const Footer = ({ children, className = "" }) => {
  return (
    <footer className={`w-full ${className}`}>
      {children}
    </footer>
  );
};

export default Footer;
