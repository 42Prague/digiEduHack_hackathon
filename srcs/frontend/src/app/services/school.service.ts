import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, of } from 'rxjs';
import { School } from '../models/school';

@Injectable({ providedIn: 'root' })
export class SchoolService {
	// #region Private Properties
	private readonly apiBase: string = '/api/schools';
	// #endregion

	// #region Public Methods
	public constructor(private readonly http: HttpClient) {}

	public list(regionId?: string): Observable<School[]> {
		return this.http.get<unknown[]>(this.apiBase).pipe(
			map((items: unknown[]) => items.map((i: unknown) => this.mapApiSchool(i))),
			map((schools: School[]) => regionId ? schools.filter(s => s.regionId === regionId) : schools)
		);
	}

	public getById(id: string): Observable<School | undefined> {
		return this.http.get<unknown>(`${this.apiBase}/${encodeURIComponent(id)}`).pipe(
			map((i: unknown) => this.mapApiSchool(i))
		);
	}

	public create(payload: Omit<School, 'id'>): Observable<School> {
		// Not supported by backend yet
		return of({ ...payload, id: '' } as School);
	}

	public update(id: string, update: Partial<School>): Observable<School | undefined> {
		// Not supported by backend yet
		return of(undefined);
	}
	// #endregion

	// #region Private Methods
	private mapApiSchool(raw: unknown): School {
		const o = raw as Record<string, unknown>;
		return {
			id: String(o['id'] ?? ''),
			regionId: String(o['region'] ?? ''),
			name: String(o['name'] ?? ''),
			address: String(o['address'] ?? ''),
			headmasterName: undefined,
			contactEmail: undefined,
			contactPhone: undefined
		};
	}
	// #endregion
}

