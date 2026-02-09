import React from "react";

const Navbar = ({ children, className = "" }) => {
  return (
    <header className={`w-full ${className}`}>
      {children}
    </header>
  );
};

export default Navbar;
