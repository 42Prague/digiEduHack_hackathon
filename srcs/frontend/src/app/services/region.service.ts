import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Region } from '../models/region';
import { map, Observable, of, throwError } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class RegionService {
	// #region Private Properties
	private readonly apiBase: string = '/api/regions';
	// #endregion

	// #region Public Methods
	public constructor(private readonly http: HttpClient) {}

	public list(): Observable<Region[]> {
		return this.http.get<unknown[]>(this.apiBase).pipe(
			map((items: unknown[]) => items.map((i: unknown) => this.mapApiRegion(i)))
		);
	}

	public getById(id: string): Observable<Region | undefined> {
		return this.http.get<unknown>(`${this.apiBase}/${encodeURIComponent(id)}`).pipe(
			map((i: unknown) => this.mapApiRegion(i))
		);
	}

	public create(payload: Omit<Region, 'id'>): Observable<void> {
		const body: Record<string, unknown> = {
			name: payload.name,
			legal_address: payload.address
			// main_contact intentionally omitted; backend will handle NULL when absent
		};
		return this.http.post<void>(this.apiBase, body);
	}

	public update(id: string, changes: Partial<Omit<Region, 'id'>>): Observable<Region | undefined> {
		// Not supported by backend yet
		return of(undefined);
	}
	// #endregion

	// #region Private Methods
	private mapApiRegion(raw: unknown): Region {
		const o = raw as Record<string, unknown>;
		return {
			id: String(o['id'] ?? ''),
			name: String(o['name'] ?? ''),
			address: String(o['legal_address'] ?? ''),
			// Backend might expose main_contact UUID; map not yet supported to email/phone
			contactEmail: undefined,
			contactPhone: undefined
		};
	}
	// #endregion
}

