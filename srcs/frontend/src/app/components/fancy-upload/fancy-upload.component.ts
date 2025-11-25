import { ChangeDetectionStrategy, Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../services/data.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { HttpEvent, HttpEventType } from '@angular/common/http';

type UploadScope = 'region' | 'school';
type UploadStatus = 'idle' | 'validating' | 'uploading' | 'success' | 'error';

@Component({
	selector: 'app-fancy-upload',
	standalone: true,
	imports: [CommonModule, FormsModule, TranslateModule],
	templateUrl: './fancy-upload.component.html',
	styleUrls: ['./fancy-upload.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class FancyUploadComponent {
	// #region Public Properties
	@Input() public scope: UploadScope = 'region';
	@Input() public defaultId: string = 'r-1';
	public scopeId: string = '';
	public selectedFile?: File;
	public status: UploadStatus = 'idle';
	public progress: number = 0;
	public dragOver: boolean = false;
	public errors: string[] = [];
	public message?: string;
	// #endregion

	// #region Private Properties
	private readonly dataService: DataService = inject(DataService);
	private readonly translate: TranslateService = inject(TranslateService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		this.scopeId = this.defaultId;
	}

	public onFileInputChange(event: Event): void {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			this.setFile(input.files[0]);
		}
	}

	public onDragOver(event: DragEvent): void {
		event.preventDefault();
		this.dragOver = true;
	}

	public onDragLeave(event: DragEvent): void {
		event.preventDefault();
		this.dragOver = false;
	}

	public onDrop(event: DragEvent): void {
		event.preventDefault();
		this.dragOver = false;
		const file = event.dataTransfer?.files?.[0];
		if (file) {
			this.setFile(file);
		}
	}

	public startUpload(): void {
		if (!this.scopeId || !this.selectedFile) {
			this.status = 'error';
			this.errors = [this.translate.instant('upload.provideIdAndFile')];
			return;
		}
		this.errors = [];
		this.status = 'validating';

		// Quick validations (size only; accept any file type)
		const errs: string[] = [];
		const maxBytes = 500 * 1024 * 1024; // 500MB limit (matches proxy)
		if (this.selectedFile.size > maxBytes) {
			errs.push(this.translate.instant('upload.fileTooLarge'));
		}
		if (errs.length > 0) {
			this.status = 'error';
			this.errors = errs;
			return;
		}

		// Real upload with progress
		this.status = 'uploading';
		this.progress = 0;
		this.dataService.uploadWithProgress(this.scope, this.scopeId, this.selectedFile as File).subscribe({
			next: (event: HttpEvent<unknown>) => {
				if (event.type === HttpEventType.UploadProgress) {
					const total = (event.total ?? (this.selectedFile as File).size) || 1;
					this.progress = Math.max(1, Math.min(99, Math.round((event.loaded / total) * 95)));
				} else if (event.type === HttpEventType.Response) {
					this.progress = 100;
					this.status = 'success';
					// Response body comes from ingest RawIngestResult
					const body: any = event.body || {};
					const id = body.raw_id || '';
					this.message = this.translate.instant('upload.successMessage', { id, scopeId: this.scopeId });
				}
			},
			error: () => {
				this.status = 'error';
				this.errors = [this.translate.instant('common.errorTryAgain')];
			}
		});
	}

	public reset(): void {
		this.selectedFile = undefined;
		this.status = 'idle';
		this.progress = 0;
		this.errors = [];
		this.message = undefined;
	}
	// #endregion

	// #region Private Methods
	private setFile(file: File): void {
		this.selectedFile = file;
		this.errors = [];
		this.status = 'idle';
	}
	// #endregion
}


