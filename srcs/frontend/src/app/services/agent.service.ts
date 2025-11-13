import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AnalysisRequest {
	query: string;
	language?: string;
	session_id?: string | null;
	max_steps?: number;
}

export interface PlotSpec {
	title?: string | null;
	x_axis?: string | null;
	y_axis?: string | null;
	series?: string | null;
	description?: string | null;
}

export interface Step {
	type: 'llm_call' | 'tool_call' | 'final';
	label: string;
	detail: string;
	tool_name?: string | null;
	tool_args?: Record<string, unknown> | null;
}

export interface AnalysisResponse {
	answer: string;
	steps: Step[];
	plot?: PlotSpec | null;
	model: string;
	token_usage?: Record<string, number> | null;
	session_id: string;
}

@Injectable({
	providedIn: 'root'
})
export class AgentService {
	private readonly baseUrl = '/agent';

	constructor(private readonly http: HttpClient) {}

	public analyze(body: AnalysisRequest): Observable<AnalysisResponse> {
		return this.http.post<AnalysisResponse>(`${this.baseUrl}/fancy_analyze`, body);
	}
}


