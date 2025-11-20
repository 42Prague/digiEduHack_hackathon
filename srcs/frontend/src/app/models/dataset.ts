export interface DatasetSummary {
	id: string;
	scope: 'region' | 'school';
	scopeId: string;
	period: string;
	records: number;
	lastUpdated: string;
}

