import { Injectable, inject } from '@angular/core';
import { Observable, map, tap } from 'rxjs';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { DatasetSummary } from '../models/dataset';

@Injectable({ providedIn: 'root' })
export class DataService {
	// #region Private Properties
	private readonly http: HttpClient = inject(HttpClient);
	private readonly datasets: DatasetSummary[] = [];
	// #endregion

	// #region Public Methods
	public listByScope(scope: 'region' | 'school', scopeId?: string): Observable<DatasetSummary[]> {
		const filtered = scopeId ? this.datasets.filter(d => d.scope === scope && d.scopeId === scopeId) : this.datasets.filter(d => d.scope === scope);
		return new Observable<DatasetSummary[]>((subscriber) => {
			subscriber.next(filtered);
			subscriber.complete();
		});
	}

	public upload(scope: 'region' | 'school', scopeId: string, _file: File): Observable<DatasetSummary> {
		type RawIngestResult = { success: boolean; raw_id?: string; has_text: boolean; has_table_data: boolean; };
		const form = new FormData();
		form.append('file', _file, _file.name);
		// Map scope into optional metadata fields understood by ingest
		form.append('doc_type', scope);
		// Only send numeric workshop_id; backend expects Optional[int]
		const numericId = Number(scopeId);
		if (Number.isFinite(numericId) && String(numericId) === scopeId.trim()) {
			form.append('workshop_id', String(numericId));
		}

		return this.http.post<RawIngestResult>('/ingest/raw/ingest', form).pipe(
			map((res: RawIngestResult) => {
				const id = res.raw_id || crypto.randomUUID();
				const created: DatasetSummary = {
					id,
					scope,
					scopeId,
					period: new Date().toISOString().slice(0, 7), // YYYY-MM
					records: res.has_table_data ? 1 : 0,
					lastUpdated: new Date().toISOString().slice(0, 10)
				};
				this.datasets.push(created);
				return created;
			})
		);
	}

	public uploadWithProgress(scope: 'region' | 'school', scopeId: string, _file: File): Observable<HttpEvent<unknown>> {
		type AnyIngestResponse = { success: boolean; raw_id?: string; audio_id?: string; inserted_rows?: number; has_text?: boolean; has_table_data?: boolean; };
		const form = new FormData();
		form.append('file', _file, _file.name);
		const name = (_file.name || '').toLowerCase();
		const isAudio = name.endsWith('.mp3');
		const isSurvey = name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xls') || name.endsWith('.json');
		const numericId = Number(scopeId);
		const sendNumeric = Number.isFinite(numericId) && String(numericId) === scopeId.trim();

		let url = '/ingest/raw/ingest';
		if (isAudio) {
			url = '/ingest/audio/upload';
			if (sendNumeric) {
				form.append('workshop_id', String(numericId));
			}
			// do not append doc_type for audio endpoint
		} else if (isSurvey) {
			url = '/ingest/survey/ingest';
			if (sendNumeric) {
				form.append('workshop_id', String(numericId));
			}
		} else {
			form.append('doc_type', scope);
			if (sendNumeric) {
				form.append('workshop_id', String(numericId));
			}
		}

		return this.http.post<AnyIngestResponse>(url, form, { observe: 'events', reportProgress: true }).pipe(
			tap((event: HttpEvent<AnyIngestResponse>) => {
				if (event.type === HttpEventType.Response && event.body) {
					const res = event.body;
					const id = res.audio_id || res.raw_id || crypto.randomUUID();
					const created: DatasetSummary = {
						id,
						scope,
						scopeId,
						period: new Date().toISOString().slice(0, 7),
						records: typeof res.inserted_rows === 'number' ? res.inserted_rows : (res.has_table_data ? 1 : 0),
						lastUpdated: new Date().toISOString().slice(0, 10)
					};
					this.datasets.push(created);
				}
			})
		);
	}
	// #endregion
}

