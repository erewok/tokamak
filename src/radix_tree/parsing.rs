use std::cmp::min;
use std::iter::zip;

use nom::error::{Error, ErrorKind, ParseError};
use nom::{Err, bytes::complete::{is_not,take_until}, IResult};
use pyo3::prelude::*;


/// Find the first non-matching index in two strings
#[pyfunction]
pub fn first_nonequal_idx(left: &str, right: &str) -> usize {
    let mut idx: usize = 0;
    let mut chars_iter = zip(left.chars(), right.chars());

    let max_search_len = min(left.len(), right.len());
    while idx < max_search_len {
        match chars_iter.next() {
            None => break,
            Some((a, b)) => {
                if a == b {
                    idx += 1;
                } else {
                    break;
                }

            }
        }
    }
    idx
}

/// Borrowed from:
/// https://github.com/Geal/nom/issues/1253#issue-751629920
pub fn take_until_unbalanced(
    opening_bracket: char,
    closing_bracket: char,
) -> impl Fn(&str) -> IResult<&str, &str> {
    move |i: &str| {
        let mut index = 0;
        let mut bracket_counter = 0;
        while let Some(n) = &i[index..].find(&[opening_bracket, closing_bracket, '\\'][..]) {
            index += n;
            let mut it = i[index..].chars();
            match it.next().unwrap_or_default() {
                c if c == '\\' => {
                    // Skip the escape char `\`.
                    index += '\\'.len_utf8();
                    // Skip also the following char.
                    let c = it.next().unwrap_or_default();
                    index += c.len_utf8();
                }
                c if c == opening_bracket => {
                    bracket_counter += 1;
                    index += opening_bracket.len_utf8();
                }
                c if c == closing_bracket => {
                    // Closing bracket.
                    bracket_counter -= 1;
                    index += closing_bracket.len_utf8();
                }
                // Can not happen.
                _ => unreachable!(),
            };
            // We found the unmatched closing bracket.
            if bracket_counter == -1 {
                // We do not consume it.
                index -= closing_bracket.len_utf8();
                return Ok((&i[index..], &i[0..index]));
            };
        }

        if bracket_counter == 0 {
            Ok(("", i))
        } else {
            Err(Err::Error(Error::from_error_kind(i, ErrorKind::TakeUntil)))
        }
    }
}
pub fn parse_url_chunk(input: &str) -> () {
    take_until("/")
}



#[cfg(test)]
mod tests {
    use super::*;
    use nom::error::ErrorKind;

    #[test]
    fn test_take_until_unmatched() {
        assert_eq!(take_until_unbalanced('(', ')')("abc"), Ok(("", "abc")));
        assert_eq!(
            take_until_unbalanced('(', ')')("url)abc"),
            Ok((")abc", "url"))
        );
        assert_eq!(
            take_until_unbalanced('(', ')')("u()rl)abc"),
            Ok((")abc", "u()rl"))
        );
        assert_eq!(
            take_until_unbalanced('(', ')')("u(())rl)abc"),
            Ok((")abc", "u(())rl"))
        );
        assert_eq!(
            take_until_unbalanced('(', ')')("u(())r()l)abc"),
            Ok((")abc", "u(())r()l"))
        );
        assert_eq!(
            take_until_unbalanced('(', ')')("u(())r()labc"),
            Ok(("", "u(())r()labc"))
        );
        assert_eq!(
            take_until_unbalanced('(', ')')(r#"u\((\))r()labc"#),
            Ok(("", r#"u\((\))r()labc"#))
        );
        assert_eq!(
            take_until_unbalanced('(', ')')("u(())r(labc"),
            Err(nom::Err::Error(nom::error::Error::new(
                "u(())r(labc",
                ErrorKind::TakeUntil
            )))
        );
        assert_eq!(
            take_until_unbalanced('€', 'ü')("€uü€€üürlüabc"),
            Ok(("üabc", "€uü€€üürl"))
        );
    }
}