/** 0 = Sunday … 6 = Saturday (matches `Date.getDay()`). */
export type WeekdayIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export type ScheduleItem = {
	id: string;
	title: string;
	courseCode?: string;
	location?: string;
	/** Day of week for this recurring slot */
	dayOfWeek: WeekdayIndex;
	/** "HH:MM" 24h */
	startTime: string;
	/** "HH:MM" 24h */
	endTime: string;
};

export type Assignment = {
	id: string;
	title: string;
	courseCode?: string;
	/** ISO date string YYYY-MM-DD */
	dueDate: string;
	completed: boolean;
};

export type FinanceCategory = "course" | "bus";

export type FinanceItem = {
	id: string;
	title: string;
	category: FinanceCategory;
	amount: number;
	currency: string;
	paid: boolean;
	/** Optional ISO date YYYY-MM-DD */
	dueDate?: string;
};
