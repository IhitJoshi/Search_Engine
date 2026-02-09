import React from "react";

const Button = ({ className = "", type = "button", ...props }) => {
  return <button type={type} className={className} {...props} />;
};

export default Button;
