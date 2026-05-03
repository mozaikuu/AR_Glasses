import type { Assignment, FinanceItem, ScheduleItem, WeekdayIndex } from "./types";

function parseTimeToMinutes(hhmm: string): number {
	const [h, m] = hhmm.split(":").map((x) => Number.parseInt(x, 10));
	if (Number.isNaN(h) || Number.isNaN(m)) {
		return 0;
	}
	return h * 60 + m;
}

export function getWeekdayIndex(date: Date): WeekdayIndex {
	return date.getDay() as WeekdayIndex;
}

/** ISO calendar date in local timezone YYYY-MM-DD */
export function toLocalISODateString(date: Date): string {
	const y = date.getFullYear();
	const mo = String(date.getMonth() + 1).padStart(2, "0");
	const d = String(date.getDate()).padStart(2, "0");
	return `${y}-${mo}-${d}`;
}

export function scheduleForDay(
	schedule: ScheduleItem[],
	date: Date,
): ScheduleItem[] {
	const dow = getWeekdayIndex(date);
	return [...schedule]
		.filter((s) => s.dayOfWeek === dow)
		.sort(
			(a, b) =>
				parseTimeToMinutes(a.startTime) - parseTimeToMinutes(b.startTime),
		);
}

export function pendingAssignments(assignments: Assignment[]): Assignment[] {
	return assignments.filter((a) => !a.completed);
}

export function overdueAssignments(
	assignments: Assignment[],
	today: Date,
): Assignment[] {
	const todayStr = toLocalISODateString(today);
	return assignments.filter(
		(a) => !a.completed && a.dueDate < todayStr,
	);
}

export type FinanceTotals = {
	courseUnpaid: number;
	coursePaid: number;
	busUnpaid: number;
	busPaid: number;
	currency: string;
};

export function financeTotals(
	items: FinanceItem[],
	fallbackCurrency = "EGP",
): FinanceTotals {
	let courseUnpaid = 0;
	let coursePaid = 0;
	let busUnpaid = 0;
	let busPaid = 0;
	let currency = fallbackCurrency;

	for (const it of items) {
		currency = it.currency || currency;
		if (it.category === "course") {
			if (it.paid) {
				coursePaid += it.amount;
			} else {
				courseUnpaid += it.amount;
			}
		} else {
			if (it.paid) {
				busPaid += it.amount;
			} else {
				busUnpaid += it.amount;
			}
		}
	}

	return { courseUnpaid, coursePaid, busUnpaid, busPaid, currency };
}

export function newId(prefix: string): string {
	return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`;
}
