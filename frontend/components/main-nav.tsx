"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
	{ href: "/", label: "Live Bus Map" },
	{ href: "/wallet", label: "Student Wallet" },
	{ href: "/capacity", label: "Capacity Dashboard" },
	{ href: "/admin", label: "Admin Panel" },
];

export function MainNav() {
	const pathname = usePathname();

	return (
		<nav className="flex flex-wrap items-center gap-2 md:gap-3">
			{links.map((link) => {
				const active = pathname === link.href;
				return (
					<Link
						key={link.href}
						href={link.href}
						className={[
							"rounded-full px-4 py-2 text-sm transition",
							active
								? "bg-mint-500/25 text-mint-300 ring-1 ring-mint-300/50"
								: "bg-white/5 text-slate-200 hover:bg-white/10",
						].join(" ")}
					>
						{link.label}
					</Link>
				);
			})}
		</nav>
	);
}
