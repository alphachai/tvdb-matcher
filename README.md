# TVDB Matcher

I threw this together to clean up my TV media. Nothing special here, but it might save you time too.

This matcher relies completely on word matching. All symbols are ignored. This is currently designed to clean up names in a format roughly focused around the actual name of the episode since those are the messiest files and the ones I'm trying to address. The next revision will match first on a S00E00 pattern and second on keywords.


## Example

### Command
```bash
python clean.py --apikey=TVDB_API_KEY --user=TVDB_USERNAME --userkey=TVDB_USER_KEY --showid=TVDB_SHOW_ID /path/to/your/media
```

### Output
```
Matched 1809 Red Riding Hoodwinked with S1955E26 "Red Riding Hoodwinked" with 100% certainty.
Matched 2306 You Dont Know What Youre Doin with S1931E13 "You Don't Know What You're Doin'!" with 100% certainty.
Matched 2302 Smile Darn Ya Smile with S1931E9 "Smile, Darn Ya, Smile!" with 100% certainty.
Matched S1956E11 Gee Whizzzzzzz with S1956E11 "Gee Whiz-z-z-z-z-z-z" with 100% certainty.
Skipping tests/72514_solved/S1956E11 Gee Whiz-z-z-z-z-z-z.mkv because tests/72514_solved/S1956E11 Gee Whiz-z-z-z-z-z-z.mkv already exists.
```
