export type HistogramSpec = {
	type: 'histogram';
	title: string;
	x_values: string[];
	y_values: number[];
	y_axis_label: string;
};

export type PieSpec = {
	type: 'pie';
	title: string;
	labels: string[];
	values: number[];
};

export type LineSpec = {
	type: 'line';
	title: string;
	x_values: string[];
	y_series: { name: string; values: number[] }[];
	y_axis_label: string;
};

export type GraphSpec = HistogramSpec | PieSpec | LineSpec;


