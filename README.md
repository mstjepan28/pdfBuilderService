Autor diplomskog rada: Stjepan Markovčić

Mentor: doc. dr. sc. Nikola Tanković

Kolegij: Izrada informatičkih projekata

Sveučilište Jurja Dobrile u Puli, Fakultet informatike

Sažetak

Cilj ovog diplomskog rada je izrada web aplikacije koja predstavlja jedan dio i jedan proces puno većeg sustava. Svrha aplikacije jest stvaranje predloška za PDF dokumente koji se zatim mogu popunjavati s podacima u svrhu generiranja PDF dokumenta. Aplikacija je rađena sa idejom da je dio puno većeg sustava koji se razvija u FIPU lab-u, taj veći sustav se oslanja na BPMN procesima. Makar je cijeli sustav zamišljen kroz BPMN procese, ova aplikacija nije jedan od procesa nego vanjski proces. To znači da korisnik putem ove aplikacije kreira PDF predložak koji se pohranjuje u bazu. Tek kada BPMN proces dođe do određenog koraka, putem API poziva generiraju se PDF dokumenti po prethodno kreiranom predlošku te se dohvaćaju. Za izradu aplikacije korišteni su VueJS2 razvojni okvir(eng. framework) i SCSS za frontend dio projekta, Python programski jezik i AIOHTTP biblioteka(eng. library) za backend dio projekta te PostgreSQL baza podataka za pohranu podataka. Razvoj aplikacije je bio vođen idejom neovisnosti aplikacije od ostatka sustava u kojemu se nalazi. Ovaj pristup olakšava integraciju aplikacije sa ostatkom sustava te ukoliko se javi potreba, uklanjanje aplikacije iz ostatka sustava.
Ključne rijeći

VueJs, SCSS, Python, PostgreSQL, AIOHTTP, PDF, web aplikacije
