import { Link, NavLink } from 'react-router'

import logo from '../../assets/layout/logo.svg'

export default function PublicHeader() {
  return (
    <header className="public-header">
      <Link className="public-header__brand" to="/">
        <img src={logo} width={48} height={48} alt="" />
        <span>Learning Tracker</span>
      </Link>
      <nav className="public-header__nav" aria-label="Điều hướng công khai">
        <NavLink to="/" end>Home</NavLink>
        <NavLink to="/login">Login</NavLink>
        <NavLink to="/register">Sign up</NavLink>
      </nav>
    </header>
  )
}
