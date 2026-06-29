/**
 * Navigation route registry — the extensibility seam. Adding a page = one route file + one
 * entry here (no other changes). `permission` is null for everyone or an RBAC role string;
 * the nav component filters entries the current role may not see.
 */
import { Home, User, Users, Briefcase, Lightbulb, Shield, type LucideIcon } from 'lucide-react'

export type NavItem = { path: string; label: string; icon: LucideIcon; permission: string | null }

export const NAV: readonly NavItem[] = [
  { path: '/home', label: 'Home', icon: Home, permission: null },
  { path: '/profile', label: 'Profile', icon: User, permission: null },
  { path: '/matches', label: 'Matches', icon: Users, permission: null },
  { path: '/grants', label: 'Grants', icon: Briefcase, permission: null },
  { path: '/ideas', label: 'Ideas', icon: Lightbulb, permission: null },
  { path: '/admin', label: 'Admin', icon: Shield, permission: 'admin' },
] as const
