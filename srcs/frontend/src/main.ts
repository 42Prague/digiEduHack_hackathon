import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, HttpClient } from '@angular/common/http';
import { AppComponent } from './app/app.component';
import { APP_ROUTES } from './app/app.routes';
import { APP_INITIALIZER, LOCALE_ID, importProvidersFrom } from '@angular/core';
import { TranslateLoader, TranslateModule, TranslateService } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { registerLocaleData } from '@angular/common';
import localeCs from '@angular/common/locales/cs';

registerLocaleData(localeCs);

export function HttpLoaderFactory(http: HttpClient): TranslateHttpLoader {
	return new TranslateHttpLoader(http, '/assets/i18n/', '.json');
}

function initTranslate(translate: TranslateService): () => Promise<void> {
	return () =>
		new Promise<void>((resolve) => {
			const saved = (localStorage.getItem('lang') || '').toLowerCase();
			const browser = (navigator.language || 'en').slice(0, 2);
			const lang = (saved === 'cs' || saved === 'en') ? saved : (browser === 'cs' ? 'cs' : 'en');
			translate.addLangs(['en', 'cs']);
			translate.setDefaultLang('en');
			translate.use(lang).subscribe({ complete: () => resolve() });
		});
}

function localeIdFactory(): string {
	const saved = (localStorage.getItem('lang') || '').toLowerCase();
	const lang = saved === 'cs' ? 'cs' : 'en';
	return lang === 'cs' ? 'cs' : 'en-US';
}

bootstrapApplication(AppComponent, {
	providers: [
		provideAnimations(),
		provideRouter(APP_ROUTES),
		provideHttpClient(),
		importProvidersFrom(
			TranslateModule.forRoot({
				loader: {
					provide: TranslateLoader,
					useFactory: HttpLoaderFactory,
					deps: [HttpClient]
				}
			})
		),
		{
			provide: APP_INITIALIZER,
			useFactory: initTranslate,
			deps: [TranslateService],
			multi: true
		},
		{
			provide: LOCALE_ID,
			useFactory: localeIdFactory
		}
	]
}).catch((err: unknown) => console.error(err));

